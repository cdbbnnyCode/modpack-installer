// Minecraft Forge Installer Hack
// Bypasses the GUI and installs the Forge client to the specified location
import java.io.File;
import java.net.URL;
import java.net.URLClassLoader;
import java.net.MalformedURLException;
import java.lang.reflect.Proxy;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationHandler;
import java.io.OutputStream;
import java.util.function.Predicate;

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

  /*
    Interfaces for each major release version:
    1.0 / 1.1 / 1.2 / 1.3:
      cpw.mods.fml.installer.ClientInstall().run(File path);
    1.5+:
      net.minecraftforge.installer.ClientInstall().run(
        File path, 
        com.google.common.base.Predicate<String> optionals
      );
    2.0:
      net.minecraftforge.installer.actions.ClientInstall(
        net.minecraftforge.installer.json.InstallV1 profile
          = net.minecraftforge.installer.json.Util.loadInstallProfile(),
        
        net.minecraftforge.installer.actions.ProgressCallback callback
      ).run(
        File path,
        java.util.function.Predicate<String> optionals,
        File installer = installer jar path
      )
  */

  private static boolean run_v1(File target, ClassLoader loader)
      throws ReflectiveOperationException
  {
    Class<?> clientInstall = null;
    try
    {
      clientInstall = Class.forName("cpw.mods.fml.installer.ClientInstall", true, loader);
    }
    catch (ClassNotFoundException e)
    {
      // must be v1.5+ or v2
      return false;
    }
    Object installer = clientInstall.getConstructor().newInstance();
    clientInstall.getDeclaredMethod("run", File.class).invoke(installer, target);

    return true;
  }

  private static boolean run_v15(File target, ClassLoader loader)
      throws ReflectiveOperationException
  {
    // "Import" the required classes
    Class<?> predicate = null;
    Class<?> clientInstall = null;

    try
    {
      predicate = Class.forName("com.google.common.base.Predicate", true, loader);
      clientInstall = Class.forName("net.minecraftforge.installer.ClientInstall", true, loader);
    }
    catch (ClassNotFoundException e)
    {
      return false;
    }

    // Make a Predicate that returns true, installing all optionals
    // This will install Mercurius unconditionally, but we might change that. TODO
    InvocationHandler handler = new ForgeHack.MInvocationHandler();
    Object pred = Proxy.newProxyInstance(loader, new Class[] {predicate}, handler);

    // Run the client install function. This will pop up a dialog and install Forge to the
    // specified Minecraft directory.
    Object install = clientInstall.getConstructor().newInstance();
    clientInstall.getDeclaredMethod("run", File.class, predicate).invoke(install, target, pred);

    return true;
  }

  private static boolean run_v2(File target, File jarfile, ClassLoader loader)
      throws ReflectiveOperationException
  {
    // classes needed
    Class<?> c_ClientInstall = null;
    Class<?> c_Util = null;
    Class<?> c_InstallV1 = null;
    Class<?> c_ProgressCallback = null;

    try
    {
      c_ClientInstall    = Class.forName("net.minecraftforge.installer.actions.ClientInstall", true, loader);
      c_Util             = Class.forName("net.minecraftforge.installer.json.Util", true, loader);
      try
      {
        c_InstallV1      = Class.forName("net.minecraftforge.installer.json.InstallV1", true, loader);
      }
      catch (ClassNotFoundException ex)
      {
        System.out.println("using v0 Install class");
        c_InstallV1      = Class.forName("net.minecraftforge.installer.json.Install", true, loader);
      }

      c_ProgressCallback = Class.forName("net.minecraftforge.installer.actions.ProgressCallback", true, loader);
    }
    catch (ClassNotFoundException e)
    {
      System.out.println(e.getMessage());
      return false;
    }

    // load the profile
    Object profile = c_Util.getDeclaredMethod("loadInstallProfile").invoke(null); // returns InstallV1 object

    

    // load the progress monitor (stdout only)
    Object monitor = c_ProgressCallback.getDeclaredMethod("withOutputs",
        OutputStream[].class).invoke(null, new Object[] { new OutputStream[] {System.out} });

    // create the ClientInstall
    Object installer = c_ClientInstall.getConstructor(c_InstallV1, c_ProgressCallback)
                      .newInstance(profile, monitor);

    // create the predicate
    Predicate<String> p = (param) -> true;

    // run the installer
    try
    {
      c_ClientInstall.getDeclaredMethod("run", File.class, Predicate.class, File.class)
        .invoke(installer, target, p, jarfile);
    }
    catch (NoSuchMethodException e)
    {
      c_ClientInstall.getDeclaredMethod("run", File.class, Predicate.class)
        .invoke(installer, target, p);
    }

    return true;
  }

  public static void main(String[] args) throws Exception
  {
    if (args.length < 2)
    {
      System.out.println("Usage: ForgeHack <jarfile> <target dir>");
      System.exit(1);
    }

    // NOTE: While this now has compatibility for all known versions of the
    // installer, older installers seem to be broken due to missing mirror servers.
    // As a result, support for any installer versions older than v2 may be
    // dropped in the near future.

    ClassLoader loader = getClassLoader(args[0]);
    File target = new File(args[1]);
    File jarfile = new File(args[0]);

    System.out.println("Attempting to launch v1.5+ installer");
    if (run_v15(target, loader))
    {
      System.out.println("Success!");
      return;
    }

    System.out.println("Attempting to launch v2 installer");
    if (run_v2(target, jarfile, loader))
    {
      System.out.println("Success!");
      return;
    }

    System.out.println("Attempting to launch v1 installer");
    if (run_v1(target, loader))
    {
      System.out.println("Success!");
      return;
    }

    System.out.println("Failed to launch installer.");
    System.exit(1);
  }
}
