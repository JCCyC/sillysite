CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -I.
LDLIBS  = -lcurl -lssl -lcrypto -lcjson -lpthread

LIB     = libsillysite.a
PROGS   = login changepw season

.PHONY: all clean

all: $(LIB) $(PROGS)

$(LIB): sillysite.o
	ar rcs $@ $^

login: login.o $(LIB)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

changepw: changepw.o $(LIB)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

season: season.o $(LIB)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

sillysite.o: sillysite.c sillysite.h
login.o:    login.c    sillysite.h readpass.h
changepw.o: changepw.c sillysite.h readpass.h
season.o:   season.c   sillysite.h

clean:
	rm -f *.o $(LIB) $(PROGS)
