// Ghidra headless post-script: dump functions, strings and decompiled C.
// Usage (via tools/ghidra_dump.sh): -postScript DumpAll.java <outfile>
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.StringDataInstance;
import java.io.*;

public class DumpAll extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        PrintWriter out = new PrintWriter(new FileWriter(args.length > 0 ? args[0] : "ghidra_dump.txt"));
        out.println("# program: " + currentProgram.getName() + "  arch: " + currentProgram.getLanguageID());
        out.println("## functions");
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        java.util.List<Function> funcs = new java.util.ArrayList<>();
        while (it.hasNext()) {
            Function f = it.next();
            funcs.add(f);
            out.printf("%s %s%s%n", f.getEntryPoint(), f.getName(), f.isThunk() ? " (thunk)" : "");
        }
        out.println("## strings");
        for (Data d : currentProgram.getListing().getDefinedData(true)) {
            if (d.hasStringValue()) {
                out.printf("%s %s%n", d.getAddress(), StringDataInstance.getStringDataInstance(d).getStringValue());
            }
        }
        out.println("## decompiled");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (Function f : funcs) {
            if (f.isThunk() || f.isExternal()) continue;
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            out.println("// ---- " + f.getName() + " @ " + f.getEntryPoint());
            if (r.decompileCompleted()) out.println(r.getDecompiledFunction().getC());
            else out.println("// decompile failed: " + r.getErrorMessage());
        }
        di.dispose();
        out.close();
    }
}
