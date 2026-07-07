#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}[*] Updating system packages...${NC}"
pkg update && pkg upgrade -y

echo -e "${YELLOW}[*] Installing dependencies (Python, Clang, Git)...${NC}"
pkg install python git clang make -y

echo -e "${YELLOW}[*] Installing Python libraries...${NC}"
pip install requests ping3 pycryptodome aiohttp cython setuptools

echo -e "${YELLOW}[*] Compiling bypass.py for your device architecture...${NC}"
# Remove old .so files to avoid confusion
rm -f bypass*.so

# Compile using Cython
python setup.py build_ext --inplace

# Clean up build directory
rm -rf build bypass.c

if [ -f bypass*.so ]; then
    echo -e "${GREEN}[+] Compilation successful!${NC}"
    # Rename to simple bypass.so for easy import
    mv bypass*.so bypass.so
    echo -e "${GREEN}[+] Running the tool...${NC}"
    python run.py
else
    echo -e "${RED}[!] Compilation failed. Please check the errors above.${NC}"
fi
