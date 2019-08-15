Records retrieved from OAI-PMH harvest for Figshare can have the following outcomes:

- Create new object in GMN (If SID is new, and thus implicitly, PID as well.)
- Update existing object in GMN (if SID exists but PID is new).
- Result in a log entry that a minor revision was not updated (If both PID and SID already exist, but the date is new).
- Be ignored entirely as already harvested (If both PID and SID exist, but date of record hasn't changed).


Plant UML diagram of logic for processing records:

plant UML::

  @startuml
  start
  :parse SID, PID, date, SciMeta
  from record in OAI-PMH harvest;
  if (SID exists in GMN?) then (yes)
    if (PID exists in GMN?) then (yes)
      if (record date for PID is 
          newer than date in GMN) then (yes)
          : log ignore minor 
            revision event;
      else (no)
          : pass;
      endif
    else (no)
    :MN.update() + 
     log update event;
    endif
  else (no) 
   : MN.create() +
     log create event;
  endif
  stop
  @enduml

