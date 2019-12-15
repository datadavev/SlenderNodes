#!/usr/bin/env bash

set -x

obliterate() {
  systemctl stop $1
  systemctl disable $1
  systemctl daemon-reload
  systemctl reset-failed
}

obliterate dataone-schema-org-scanner-worker
obliterate dataone-schema-org-scanner

rm -rf dataone*wants*

