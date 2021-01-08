#!/bin/bash

# (un)comment the Algorithm you want to use
#algo='rs'
#algo='lb'
#algo='sp'

# use GNU parallel to run multiple repetitions and scenarios in parallel
# run from project root! (where Readme is)

# DO NOT try to parallelize running sp and lb; the files are saved to the same place and hard (impossible?) to distinguish; run first sp, then lb
parallel --bar 'sp' ::: "--network" :::: scripts/network_files.txt ::: "--service_functions" :::: scripts/service_files.txt ::: "--config" :::: scripts/config_files.txt ::: "--iterations" ::: "200" ::: "--seed" :::: scripts/30seeds.txt
