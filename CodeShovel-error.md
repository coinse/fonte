# Steps to reproduce the incorrect behaviour of CodeShovel
**You first need to run the docker container using the provided image file. See `README.md`.**

The error is occurred while extracting the history of the method `equals` in `src/main/java/org/apache/commons/lang3/StringUtils.java`:
```java 
    public static boolean equals(CharSequence cs1, CharSequence cs2) { // 781
        return cs1 == null ? cs2 == null : cs1.equals(cs2);            // 782
    }                                                                  // 783
```

To reproduce the error, first check out the buggy version of Lang-14b to `/tmp/Lang-14b`.
```bash
# in a bash session of the container
defects4j checkout -p Lang -v 14b -w /tmp/Lang-14b
cd /tmp/Lang-14b
git reset --hard c8afaa3e869cc8c25577641553e0d0b5bdac78b5
```

If you use `git log` to retrieve the method histories:
```bash
git log -L781,783:src/main/java/org/apache/commons/lang3/StringUtils.java
```
it returns three commits:
- cf2e48a05c250feb636dd337dae1ffb7a1d9d411
- f349629500ff5a85683dff0a807ff8e9b5b88809
- d23b22c78078ee7468e797e80188ae9508c0eee0

Now, let us run `CodeShovel` to retrieve the histories:
```bash
java -Xmx2g -jar /root/workspace/tools/codeshovel-1.0.0-SNAPSHOT.jar -repopath /tmp/Lang-14b -filepath src/main/java/org/apache/commons/lang3/StringUtils.java -methodname equals -startline 781 -outfile output.json
```
The output then is as follows:
```txt
#########################################################################
STARTING ANALYSIS FOR FILE src/main/java/org/apache/commons/lang3/StringUtils.java
-------------------------------------------------------------------------
STARTING ANALYSIS FOR METHOD equals
====================================================
Running Analysis
Commit: HEAD
Method: equals
Lines: 781-783
====================================================

CodeShovel Change History:
fec5e47638aeb2860a604daa0f424a91dbd9a166:Yintroduced(fec5e4:equals:752)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%% RESULT %%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
"fec5e47638aeb2860a604daa0f424a91dbd9a166": "Yintroduced",
FINISHED ANALYSIS FOR METHOD equals
RESULT FILE WRITTEN TO output.json
-------------------------------------------------------------------------
FINISHED ANALYSIS FOR FILE src/main/java/org/apache/commons/lang3/StringUtils.java
#########################################################################
Total duration: 11373
```

The retrieved commit `fec5e47` is actually not related to the target method:
```diff
diff --git a/src/main/java/org/apache/commons/lang3/StringUtils.java b/src/main/java/org/apache/commons/lang3/StringUtils.java
index 73aabe4..1ecf255 100644
--- a/src/main/java/org/apache/commons/lang3/StringUtils.java
+++ b/src/main/java/org/apache/commons/lang3/StringUtils.java
@@ -6491,14 +6491,4 @@ public class StringUtils {
         }
     }
 
-    static boolean regionMatchesSequence(CharSequence cs, boolean ignoreCase, int thisStart, 
-                                         CharSequence substring, int start, int length)
-    {
-        if (cs instanceof String) {
-            return ((String) cs).regionMatches(ignoreCase, thisStart, substring, start, length);
-        } else {
-            // TODO: Implement rather than convert to String
-            return cs.toString().regionMatches(ignoreCase, thisStart, substring, start, length);
-    }
-
 }
 ```