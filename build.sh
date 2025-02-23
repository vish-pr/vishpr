if [ ! -d "venv" ] || [ "$1" = "--install" ] ; then
    python3 -m venv venv
    source venv/bin/activate
    pip3 install -r requirements.txt
else
    source venv/bin/activate
fi
