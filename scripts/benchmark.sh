#!/bin/bash
if [ ! -d "wrk" ]; then
    sudo apt-get install -y git # Install git package
    git clone https://github.com/wg/wrk.git
    cd wrk || exit 1
    make -j `nproc` > /dev/null 2>&1 || exit 1
    cd ..
fi

./wrk/wrk $@
