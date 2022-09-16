package analyzer;

import com.github.javaparser.utils.SourceRoot;

import org.openrewrite.InMemoryExecutionContext;
import org.openrewrite.Recipe;
import org.openrewrite.Result;
import org.openrewrite.java.JavaParser;
import org.openrewrite.config.Environment;
import org.openrewrite.java.tree.J;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import java.io.FileWriter;
import java.io.IOException;

import static java.util.Collections.emptyList;

public class RewriteRunner {
    public static void main(String[] args) {
        final InMemoryExecutionContext ctx = new InMemoryExecutionContext();
        final List<Path> paths = List.of(Paths.get(args[0]));

        final JavaParser javaParser =
            JavaParser.fromJavaVersion()
                .logCompilationWarningsAndErrors(false)
                .build();

        final List<J.CompilationUnit> cus = javaParser.parse(paths, null, ctx);

        Environment environment = Environment.builder().scanRuntimeClasspath().build();
        Recipe recipe = environment.activateRecipes(
            "org.openrewrite.java.cleanup.Cleanup");

        final List<Result> results = recipe.run(cus);

        // results.forEach(result -> System.out.println(result.diff()));

        // Write to output file
        try {
            FileWriter fw = new FileWriter(args[1]);
            for (Result result: results) {
                fw.write(result.diff());
            }
            fw.close();
        } catch (IOException e) {
            System.out.println("An error occurred.");
            e.printStackTrace();
        }
    }
}
