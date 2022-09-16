package analyzer;

import com.github.gumtreediff.client.Run;
import com.github.gumtreediff.matchers.MappingStore;
import com.github.gumtreediff.matchers.Matcher;
import com.github.gumtreediff.matchers.Matchers;
import com.github.gumtreediff.tree.Tree;
import com.github.gumtreediff.gen.javaparser.JavaParserGenerator;

import java.io.IOException;

public class ASTIsomorphicChecker {
    public static void main( String[] args ) throws IOException {
        Run.initGenerators(); // registers the available parsers
        String srcFile = args[0];
        String dstFile = args[1];
        Tree src = new JavaParserGenerator().generateFrom().file(srcFile).getRoot();
        Tree dst = new JavaParserGenerator().generateFrom().file(dstFile).getRoot();
        boolean isIsomorphic = src.isIsomorphicTo(dst);
        System.out.println(isIsomorphic);
    }
}
