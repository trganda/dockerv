import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Paths;

public class AttackerServer {
    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(System.getProperty("port", "8000"));
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
        server.createContext("/", ex -> {
            byte[] body = Files.readAllBytes(Paths.get("/www/probe"));
            System.out.println("[attacker] " + ex.getRequestMethod() + " " + ex.getRequestURI()
                    + " from " + ex.getRemoteAddress() + " -> serving probe (" + body.length + " bytes)");
            ex.getResponseHeaders().set("Content-Type", "application/java-archive");
            ex.sendResponseHeaders(200, body.length);
            ex.getResponseBody().write(body);
            ex.close();
        });
        server.start();
        System.out.println("[attacker] serving on :" + port);
    }
}
