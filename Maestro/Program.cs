using System.Diagnostics;

class MaestroApp : ApplicationContext
{
    private readonly NotifyIcon trayIcon;
    private Process? llamaProcess;
    private readonly string llamaArgs = "-d Ubuntu bash -c \"cd /mnt/g/llamacpp && ./llama-server -m /mnt/g/Models/solar-10.7b-v1.0.Q5_K_M.gguf --host 0.0.0.0 --port 11434 --n-gpu-layers 40 --ctx-size 4096 --threads 8 --parallel 4 --mlock\"";

    public MaestroApp()
    {
        trayIcon = new NotifyIcon()
        {
            Icon = new Icon("maestro.ico"),
            ContextMenuStrip = new ContextMenuStrip(),
            Text = "Maestro",
            Visible = true
        };

        trayIcon.ContextMenuStrip.Items.Add("Start LLaMA", null, (s, e) => StartLlama());
        trayIcon.ContextMenuStrip.Items.Add("Stop LLaMA", null, (s, e) => StopLlama());
        trayIcon.ContextMenuStrip.Items.Add("Restart LLaMA", null, (s, e) => { StopLlama(); StartLlama(); });
        trayIcon.ContextMenuStrip.Items.Add(new ToolStripSeparator());
        trayIcon.ContextMenuStrip.Items.Add("Exit", null, (s, e) => ExitApp());
    }

    private void StartLlama()
    {
        if (llamaProcess != null && !llamaProcess.HasExited)
        {
            MessageBox.Show("llama-server is already running.");
            return;
        }

        llamaProcess = new Process();
        llamaProcess.StartInfo.FileName = "wsl";
        llamaProcess.StartInfo.Arguments = llamaArgs;
        llamaProcess.StartInfo.UseShellExecute = false;
        llamaProcess.StartInfo.CreateNoWindow = true;
        llamaProcess.Start();
    }

    private void StopLlama()
    {
        if (llamaProcess != null && !llamaProcess.HasExited)
        {
            llamaProcess.Kill(true);
            llamaProcess.Dispose();
            llamaProcess = null;
        }
    }

    private void ExitApp()
    {
        StopLlama();
        trayIcon.Visible = false;
        Application.Exit();
    }
}

internal static class Program
{
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new MaestroApp());
    }
}
