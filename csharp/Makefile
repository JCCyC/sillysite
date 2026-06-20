MCS = mcs
LIB = Sillysite.dll

.PHONY: all clean

all: $(LIB) Login.exe ChangePw.exe

# Readpass.cs has no public/library API of its own (internal, like
# c/readpass.h) -- compiled directly into each program below rather than
# into the shared library, the same split as c/'s Makefile (login.o and
# changepw.o each include readpass.h themselves; there's no readpass.o).
$(LIB): Sillysite.cs
	$(MCS) -target:library -r:System.Net.Http.dll -out:$(LIB) Sillysite.cs

Login.exe: Login.cs Readpass.cs $(LIB)
	$(MCS) -r:$(LIB) -out:Login.exe Login.cs Readpass.cs

ChangePw.exe: ChangePw.cs Readpass.cs $(LIB)
	$(MCS) -r:$(LIB) -out:ChangePw.exe ChangePw.cs Readpass.cs

clean:
	rm -f *.dll *.exe *.mdb
