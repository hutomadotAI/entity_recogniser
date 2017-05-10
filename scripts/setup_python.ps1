# A script to setup a Python 3.5 virtual environment
# So that project Python setup doesn't mess up main machine
# or other projects.
$ErrorActionPreference = "Stop"

$SCRIPT_DIR=$PSScriptRoot
$ROOT_DIR="${SCRIPT_DIR}/.."
$SOURCE_DIR="${ROOT_DIR}/src"
$VE_DIR="${ROOT_DIR}/venv/entity_win"


if (-not (Test-Path $VE_DIR))
{
	Write-Host "Initializing virtualenv at $VE_DIR"
	py -3 -m venv $VE_DIR
}

Write-Host "Entering Python 3.5 virtual environment at $VE_DIR"
& $VE_DIR/Scripts/activate.ps1
pip install --upgrade pip
pushd ${SOURCE_DIR}
pip install --upgrade -r "requirements_test.txt"
pip install -e .
popd
