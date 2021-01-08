#!/bin/bash

# (un)comment the Algorithm you want to use
#algo='rs'
#algo='lb'
#algo='sp'

# use GNU parallel to run multiple repetitions and scenarios in parallel
# run from project root! (where Readme is)
parallel --bar :::: scripts/algo.txt ::: "--network" :::: scripts/network_files.txt ::: "--service_functions" :::: scripts/service_files.txt ::: "--config" :::: scripts/config_files.txt ::: "--iterations" ::: "1000" ::: "--seed" :::: scripts/30seeds.txt
