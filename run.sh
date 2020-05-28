#!/bin/bash

#mkdir ext/plaintext_policies
docker run -v "$(pwd)/ext:/ext" benandow/pol-analysis
