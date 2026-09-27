using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Threading;

namespace MaxIM
{
    class Program
    {
        static Process backendProc = null;
        static Process frontendProc = null;
        static bool isShuttingDown = false;

        static void Main(string[] args)
        {
            Console.Title = "MaxIM V2 — Sovereign AI Executive Assistant";
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("====================================================================");
            Console.WriteLine("          MaxIM V2 — Sovereign Personal AI Assistant                ");
            Console.WriteLine("====================================================================");
            Console.ResetColor();

            string rootDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
            string pythonExe = Path.Combine(rootDir, "backend", ".venv", "Scripts", "python.exe");
            string backendDir = Path.Combine(rootDir, "backend");
            string frontendDir = Path.Combine(rootDir, "frontend");

            Console.WriteLine("\n[*] Root Directory: " + rootDir);

            // 1. Verify Virtual Environment
            if (!File.Exists(pythonExe))
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("[!] Backend virtualenv not found at " + pythonExe);
                Console.WriteLine("[*] Initializing virtualenv and installing requirements...");
                Console.ResetColor();

                ProcessStartInfo venvSetup = new ProcessStartInfo("cmd.exe", "/c python -m venv \"" + Path.Combine(backendDir, ".venv") + "\" && \"" + pythonExe + "\" -m pip install -r \"" + Path.Combine(backendDir, "requirements.txt") + "\"");
                venvSetup.WorkingDirectory = rootDir;
                venvSetup.UseShellExecute = false;
                Process p = Process.Start(venvSetup);
                p.WaitForExit();
            }

            // 2. Setup shutdown hook
            Console.CancelKeyPress += (sender, e) =>
            {
                e.Cancel = true;
                Shutdown(rootDir);
                Environment.Exit(0);
            };

            AppDomain.CurrentDomain.ProcessExit += (sender, e) =>
            {
                Shutdown(rootDir);
            };

            // 3. Start Backend
            Console.WriteLine("[*] Starting MaxIM Backend API on http://127.0.0.1:8000 ...");
            ProcessStartInfo bInfo = new ProcessStartInfo("cmd.exe", "/c cd /d \"" + backendDir + "\" && \"" + pythonExe + "\" -m uvicorn server:app --host 127.0.0.1 --port 8000");
            bInfo.WorkingDirectory = backendDir;
            bInfo.WindowStyle = ProcessWindowStyle.Minimized;
            backendProc = Process.Start(bInfo);

            // 4. Start Frontend
            Console.WriteLine("[*] Starting MaxIM React 19 Frontend on http://localhost:5173 ...");
            ProcessStartInfo fInfo = new ProcessStartInfo("cmd.exe", "/c cd /d \"" + frontendDir + "\" && npm run dev");
            fInfo.WorkingDirectory = frontendDir;
            fInfo.WindowStyle = ProcessWindowStyle.Minimized;
            frontendProc = Process.Start(fInfo);

            // 5. Health Check
            Console.WriteLine("[*] Waiting for services to initialize...");
            bool healthy = false;
            for (int i = 0; i < 30; i++)
            {
                try
                {
                    HttpWebRequest req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:8000/api/health");
                    req.Timeout = 1000;
                    using (HttpWebResponse resp = (HttpWebResponse)req.GetResponse())
                    {
                        if (resp.StatusCode == HttpStatusCode.OK)
                        {
                            healthy = true;
                            break;
                        }
                    }
                }
                catch
                {
                    Thread.Sleep(500);
                }
            }

            if (healthy)
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("[v] Backend is healthy and ready.");
                Console.ResetColor();
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("[!] Health check timed out, proceeding to open browser.");
                Console.ResetColor();
            }

            // 6. Launch Browser
            Console.WriteLine("[*] Opening default browser to http://localhost:5173 ...");
            Thread.Sleep(1500);
            try
            {
                Process.Start(new ProcessStartInfo("http://localhost:5173") { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                Console.WriteLine("[!] Could not auto-launch browser: " + ex.Message);
            }

            // 7. Status Banner
            Console.Clear();
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("====================================================================");
            Console.WriteLine("          MaxIM V2 — Sovereign Personal AI Assistant                ");
            Console.WriteLine("====================================================================");
            Console.ResetColor();
            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("  [+] Frontend UI:     http://localhost:5173");
            Console.WriteLine("  [+] Backend API:     http://127.0.0.1:8000");
            Console.WriteLine("  [+] API Swagger:     http://127.0.0.1:8000/docs");
            Console.ResetColor();
            Console.WriteLine("  [+] Vault Synapse:   " + Path.Combine(rootDir, "vault"));
            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("====================================================================");
            Console.WriteLine("  MaxIM is running in the background.");
            Console.WriteLine("  Press [ENTER] or [Q] to stop all services and exit.");
            Console.WriteLine("====================================================================");
            Console.ResetColor();
            Console.WriteLine();

            while (true)
            {
                ConsoleKeyInfo key = Console.ReadKey(true);
                if (key.Key == ConsoleKey.Enter || key.Key == ConsoleKey.Q || key.Key == ConsoleKey.Escape)
                {
                    break;
                }
            }

            Shutdown(rootDir);
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("[v] MaxIM shutdown complete. Goodbye!");
            Console.ResetColor();
            Thread.Sleep(1000);
        }

        static void Shutdown(string rootDir)
        {
            if (isShuttingDown) return;
            isShuttingDown = true;
            Console.WriteLine("\n[*] Gracefully stopping all MaxIM services...");

            try
            {
                if (backendProc != null && !backendProc.HasExited)
                {
                    KillProcessTree(backendProc.Id);
                }
            }
            catch { }

            try
            {
                if (frontendProc != null && !frontendProc.HasExited)
                {
                    KillProcessTree(frontendProc.Id);
                }
            }
            catch { }

            // Release ports 8000 and 5173
            string stopBat = Path.Combine(rootDir, "stop_maxim.bat");
            if (File.Exists(stopBat))
            {
                try
                {
                    ProcessStartInfo psi = new ProcessStartInfo(stopBat)
                    {
                        WindowStyle = ProcessWindowStyle.Hidden,
                        UseShellExecute = true
                    };
                    Process p = Process.Start(psi);
                    p.WaitForExit(5000);
                }
                catch { }
            }
        }

        static void KillProcessTree(int pid)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo("taskkill", "/F /T /PID " + pid)
                {
                    WindowStyle = ProcessWindowStyle.Hidden,
                    CreateNoWindow = true,
                    UseShellExecute = false
                };
                Process p = Process.Start(psi);
                p.WaitForExit(3000);
            }
            catch { }
        }
    }
}
