  440  systemctl -v start dataone-schema-org-scanner.service 
  441  systemctl -v restart dataone-schema-org-scanner.service 
  442  systemctl list
  443  systemctl list-units
  444  systemctl remove dataone*
  445  systemctl enable dataone-schema-org-scanner-worker\@.service 
  446  systemctl enable dataone-schema-org-scanner.service 
  447  systemctl start dataone-schema-org-scanner.service
  448  ps auxg
  449  systemctl restart dataone-schema-org-scanner.service
  450  systemctl stop dataone-schema-org-scanner-worker
  451  systemctl stop dataone-schema-org-scanner-workers
  452  systemctl stop dataone-schema-org-scanner-worker*
  453  systemctl stop dataone-schema-org-scanner-worker\@.service 
  454  systemctl stop dataone-schema-org-scanner-worker@{1..10}
  455  journalctl -xe
  456  /var/local/dataone/schema_org_scan/d1_schema_scan/service-start-workers.sh
  457  cat dataone-schema-org-scanner
  458  cat dataone-schema-org-scanner.service
  459  journalctl 
  460  service --list-all
  461  service --all
  462  service --help
  463  service --status-all
  464  systemctl stop dataone-schema-org-scanner
  465  systemctl stop dataone-schema-org-scanner-worker{@0..9}
  466  systemctl stop dataone-schema-org-scanner-worker{@0..9}.service
  467  systemctl start dataone-schema-org-scanner-worker@{1..10}
  468  vim *da*work*
  469  ps auxg | grep worker
  470  systemctl disable dataone*
  471  systemctl disable  dataone-schema-org-scanner-worker@{1..10}
  472  systemctl disable  dataone-schema-org-scanner-worker@{1..10}.service
  473  systemctl disable 'dataone-schema-org-scanner-worker@7.service'
  474  systemctl | grep -i data
  475  vim rm-dataone-services.sh
  476  chmod 755 rm-dataone-services.sh 
  477  ll dataone_schema_org_scanner.service.wants/
  478  cd dataone_schema_org_scanner.service.wants/
  479  ls
  480  ls -al
  481  cat dataone-schema-org-scanner.worker.service 
  482  rm *
  483  cd ..
  484  rmdir dataone_schema_org_scanner.service.wants/
  485  dir
  486  systemctl  -e
  487  systemctl -e
  488  cat dataone-schema-org-scanner-worker\@.service 
  489  vim dataone-schema-org-scanner-worker\@.service 
  490  systemctl restart  dataone-schema-org-scanner-worker@{1..9}
  491  systemctl disable  dataone-schema-org-scanner-worker@{1..9}
  492  systemctl stop dataone-schema-org-scanner-worker@{1..9}.service
  493  systemctl disable  dataone-schema-org-scanner-worker@{1..9}.service
  494  cat ob
  495  cat rm-dataone-services.sh 
  496  rs dataone-schema-org-scanner* rm-dataone-services.sh ~
  497  vim rm-dataone-services.sh 
  498  systemctl 
  499  systemctl | cat
  500  cat --help | less
  501  systemctl | cat --paging=never
  502  systemctl | grep dataone
  503  cat dataone*service
  504  systemctl enable  dataone-schema-org-scanner
  505  systemctl restart dataone-schema-org-scanner
  506  vim *worker*
  507  vim dataone-schema-org-scanner.service
  508  systemctl disable dataone*slice
  509  ll /system.slice/
  510  systemctl remove /system.slice/system-dataone\x2dschema\x2dorg\x2dscanner\x2dworker.slice
  511  systemctl remove system.slice/system-dataone\x2dschema\x2dorg\x2dscanner\x2dworker.slice
  512  systemctl disable system.slice/system-dataone\x2dschema\x2dorg\x2dscanner\x2dworker.slice
  513  systemctl disable dataaone.dschema.org.scanner.worker.slice
  514  locate slice
  515  locate slice | grep one
  516  locate slice | grep schema
  517  locate slice | grep ema
  518  systemd-cgtop 
  519  locate slice | grep e
  520  find /lib/systemd/system/
  521  find /lib/systemd/system/ | grep slice
  522  find /lib/systemd/system/ | grep one
  523  updatedb
  524  systemd
  525  systemctl
  526  man systemctl
  527  ps auxg  grep slice
  528  ps auxg | grep slice
  529  find /var/log/ -mmin -15
  530  find /var/log/ -mmin -15 -exec tail -f {} \;
  531  systemctl daemon-reload
  532  ll
  533  ./rm-dataone-services.sh 
  534  systemctl enable  dataone-schema-org-scanner-worker@{1..9}
  535  systemctl start  dataone-schema-org-scanner-worker@{1..9}
  536  find /var/log/ -mmin -15 -exec tail -f {} +
  537  history | tail 100
  538  history | tail -100
  539  history | tail -100 > setup.sh
