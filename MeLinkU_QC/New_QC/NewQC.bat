net use W: /delete /yes
TIMEOUT /T 3
net use W: "\\10.9.8.100\LOG\QC\D" P@ssw0rd /user:"Administrator"
TIMEOUT /T 2
xcopy D:\melink\NewQC\log\*.* W:\ /D/Y/E/C/I/K/H
TIMEOUT /T 3
net use W: /delete /yes
TIMEOUT /T 2
net use W: "\\10.9.8.100\NewQC" P@ssw0rd /user:"Administrator"
TIMEOUT /T 2
xcopy W:\*.* d:\melink\NewQC\ /Y/D/E
TIMEOUT /T 3
start /D "D:\melink\NewQC" melink.exe


