#!/bin/zsh
export AWS_ACCESS_KEY_ID=$(security find-generic-password -a trellis -s AWS_ACCESS_KEY_ID -w)
export AWS_SECRET_ACCESS_KEY=$(security find-generic-password -a trellis -s AWS_SECRET_ACCESS_KEY -w)
exec litestream replicate -config "$(dirname "$0")/litestream.yml"
