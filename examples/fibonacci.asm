PUSH 1
PUSH 1
DUP
STORE 0
L1:
ADD

DUP
LOAD 0
GTR
IFZR L2

LOAD 0
SWAP
DUP
STORE 0
GOTO L1

L2:
NOP
GOTO L2