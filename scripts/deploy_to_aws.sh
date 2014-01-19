#!/bin/bash

AWS_STICKYSYNC=ec2-54-200-19-165.us-west-2.compute.amazonaws.com

ssh $AWS_STICKYSYNC "cd sticky-sync && sh scripts/stop_production_server.sh && git pull && sh scripts/start_production_server.sh"
