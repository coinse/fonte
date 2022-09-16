package analyzer;

import com.github.gumtreediff.client.Run;
import com.github.gumtreediff.matchers.MappingStore;
import com.github.gumtreediff.matchers.Matcher;
import com.github.gumtreediff.matchers.Matchers;
import com.github.gumtreediff.tree.Tree;
import com.github.gumtreediff.gen.javaparser.JavaParserGenerator;
import com.github.gumtreediff.actions.EditScriptGenerator;
import com.github.gumtreediff.actions.SimplifiedChawatheScriptGenerator;
import com.github.gumtreediff.actions.EditScript;

import java.io.IOException;

public class ASTComparator {
    public static void main( String[] args ) throws IOException {
        Run.initGenerators(); // registers the available parsers
        String srcFile = args[0];
        String dstFile = args[1];
        Tree src = new JavaParserGenerator().generateFrom().file(srcFile).getRoot();
        Tree dst = new JavaParserGenerator().generateFrom().file(dstFile).getRoot();
        // boolean isIsomorphic = src.isIsomorphicTo(dst);
        // System.out.println(isIsomorphic);
        // System.out.println("----------------------------------");
        // System.out.println(src.toTreeString());
        // System.out.println("----------------------------------");
        // System.out.println(dst.toTreeString());
        // System.out.println("----------------------------------");

        // retrieves the default matcher
        Matcher defaultMatcher = Matchers.getInstance().getMatcher();
        // computes the mappings between the trees
        MappingStore mappings = defaultMatcher.match(src, dst);
        // instantiates the simplified Chawathe script generator 
        EditScriptGenerator editScriptGenerator = new SimplifiedChawatheScriptGenerator();
        // computes the edit script
        EditScript actions = editScriptGenerator.computeActions(mappings);
        for (int i = 0; i < actions.size(); i++)
            System.out.println(actions.get(i));
    }

}
