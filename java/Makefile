JAVAC   = javac
SOURCES = Sillysite.java Readpass.java Login.java ChangePw.java

.PHONY: all clean

all: classes.stamp

# javac compiles all listed sources together (and only needs running once,
# producing every .class file in one invocation) -- a sentinel file marks
# that done, rather than a pattern rule that would otherwise re-invoke
# javac once per .class file.
classes.stamp: $(SOURCES)
	$(JAVAC) $(SOURCES)
	touch classes.stamp

clean:
	rm -f *.class classes.stamp
