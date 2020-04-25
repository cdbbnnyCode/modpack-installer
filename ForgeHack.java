// Minecraft Forge Installer Hack
// Bypasses the GUI and installs the Forge client to the specified location
import java.io.File;
import java.net.URL;
import java.net.URLClassLoader;
import java.net.MalformedURLException;
import java.util.Arrays;
import java.lang.reflect.Proxy;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationHandler;

public class ForgeHack
{
  private static ClassLoader getClassLoader(String jarfile)
  {
    try
    {
      URL url = new File(jarfile).toURI().toURL();
      return new URLClassLoader(new URL[] {url}, ForgeHack.class.getClassLoader());
    }
    catch (MalformedURLException e)
    {
      return null;
    }
  }

  private static class MInvocationHandler implements InvocationHandler
  {
    public Object invoke(Object proxy, Method method, Object[] args)
    {
      return true; // So stupid, but necessary
    }
  }

  public static void main(String[] args) throws Exception
  {
    if (args.length < 2)
    {
      System.out.println("Usage: ForgeHack <jarfile> <target dir>");
      System.exit(1);
    }

    // TODO: This program is written for the v1.5 Forge installer, which is used
    // for 1.11 and 1.12 and possibly more. Earlier versions may be compatible, but
    // the v2.0 installer seems to be rewritten and will need a different interfacing
    // algorithm. FORTUNATELY, most popular mods/packs are written for 1.12.2 these
    // days.

    ClassLoader loader = getClassLoader(args[0]);
    // "Import" the required classes
    Class predicate = Class.forName("com.google.common.base.Predicate", true, loader);
    Class clientInstall = Class.forName("net.minecraftforge.installer.ClientInstall", true, loader);

    // Make a Predicate that returns true, installing all optionals
    // This will install Mercurius unconditionally, but we might change that. TODO
    InvocationHandler handler = new ForgeHack.MInvocationHandler();
    Object pred = Proxy.newProxyInstance(loader, new Class[] {predicate}, handler);

    // Run the client install function. This will pop up a dialog and install Forge to the
    // specified Minecraft directory.
    File target = new File(args[1]);
    Object install = clientInstall.newInstance();
    clientInstall.getDeclaredMethod("run", File.class, predicate).invoke(install, target, pred);
  }
}
