#!/bin/bash
function check_return_code {
    return_code=$?;
    if [[ $return_code != 0 ]]; then
        echo "*** setup_python.sh: previous command failed, exiting ***"
        exit $return_code;
    fi
}

POSITIONAL=()
while [[ $# -gt 0 ]]
    do
    key="$1"

    case $key in
        --style-only)
        STYLE_ONLY=true
        shift # past value
        ;;
        *)    # unknown option
        POSITIONAL+=("$1") # save it in an array for later
        shift # past argument
        ;;
    esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# A script to setup a Python 3.5 virtual environment
# So that project Python setup doesn't mess up main machine
# or other projects.
SCRIPT_DIR=`dirname $BASH_SOURCE`
ROOT_DIR="${SCRIPT_DIR}/.."
SOURCE_DIR="${ROOT_DIR}/src"
VE_DIR="${ROOT_DIR}/venv/entity_unix"
if [ ! -d $VE_DIR ]; then
    echo Initializing virtualenv at $VE_DIR
	python3.5 -m venv $VE_DIR
    check_return_code
fi

echo Entering Python 3.5 virtual environment at $VE_DIR
source $VE_DIR/bin/activate
pip install --upgrade pip
check_return_code

if [ "$STYLE_ONLY" = true ]; then
    pip install --upgrade -r ${SOURCE_DIR}/requirements_code_style.txt
    check_return_code
    return
fi

pushd ${SOURCE_DIR}
pip install --upgrade -r requirements_test.txt
check_return_code
popd
python ${SOURCE_DIR}/initialize_spacy_model.py
pip install -e ${SOURCE_DIR}
check_return_code
