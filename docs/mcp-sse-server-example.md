# MCP SSE Server Example

## Program.cs

```csharp
using TestServerWithHosting.Tools;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddMcpServer()
    .WithTools<EchoTool>()
    .WithTools<SampleLlmTool>();

var app = builder.Build();

app.MapMcp();

app.Run();
```

## AspNetCoreSseServer.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <PublishAot>true</PublishAot>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\src\ModelContextProtocol\ModelContextProtocol.csproj" />
    <ProjectReference Include="..\..\src\ModelContextProtocol.AspNetCore\ModelContextProtocol.AspNetCore.csproj" />
  </ItemGroup>

</Project>
```

## SampleLlmTool.cs

```csharp
using Microsoft.Extensions.AI;
using ModelContextProtocol.Server;
using System.ComponentModel;

namespace TestServerWithHosting.Tools;

/// <summary>
/// This tool uses dependency injection and async method
/// </summary>
[McpServerToolType]
public sealed class SampleLlmTool
{
    [McpServerTool(Name = "sampleLLM"), Description("Samples from an LLM using MCP's sampling feature")]
    public static async Task<string> SampleLLM(
        IMcpServer thisServer,
        [Description("The prompt to send to the LLM")] string prompt,
        [Description("Maximum number of tokens to generate")] int maxTokens,
        CancellationToken cancellationToken)
    {
        ChatMessage[] messages =
        [
            new(ChatRole.System, "You are a helpful test server."),
            new(ChatRole.User, prompt),
        ];

        ChatOptions options = new()
        {
            MaxOutputTokens = maxTokens,
            Temperature = 0.7f,
        };

        var samplingResponse = await thisServer.AsSamplingChatClient().GetResponseAsync(messages, options, cancellationToken);

        return $"LLM sampling result: {samplingResponse}";
    }
}
```

## EchoTool.cs

```csharp
using ModelContextProtocol.Server;
using System.ComponentModel;

namespace TestServerWithHosting.Tools;

[McpServerToolType]
public sealed class EchoTool
{
    [McpServerTool, Description("Echoes the input back to the client.")]
    public static string Echo(string message)
    {
        return "hello " + message;
    }
}
```
