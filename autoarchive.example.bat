@ECHO off

"E:\py-virtualenv\autoarchive35\Scripts\python.exe" "E:\py-projects\autoarchive\autoarchive.py" -v DEBUG -l DEBUG -ls run %1 "rules_sets\default.json" -dd 1
PAUSE
