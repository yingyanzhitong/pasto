// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Pasto",
    defaultLocalization: "en",
    platforms: [.macOS(.v14)],
    products: [
        .library(name: "PastoCore", targets: ["PastoCore"]),
        .executable(name: "Pasto", targets: ["Pasto"]),
        .executable(name: "PastoHelper", targets: ["PastoHelper"]),
        .executable(name: "pasto-mcp", targets: ["PastoMCP"]),
        .executable(name: "pasto-core-tests", targets: ["PastoCoreTests"])
    ],
    targets: [
        .binaryTarget(name: "Sparkle",
                      url: "https://github.com/sparkle-project/Sparkle/releases/download/2.10.1/Sparkle-for-Swift-Package-Manager.zip",
                      checksum: "4c2e48a3e50ebcc2c88a58a4c7264a1a99c3c31857ce754357afb9cdb323022a"),
        .target(name: "PastoObjC", publicHeadersPath: "include"),
        .target(name: "PastoCore", dependencies: ["PastoObjC"], resources: [.process("Resources"), .copy("OriginalStackIcons.bundle")]),
        .executableTarget(name: "Pasto", dependencies: ["PastoCore", "PastoObjC", "Sparkle"]),
        .executableTarget(name: "PastoHelper"),
        .executableTarget(name: "PastoMCP", dependencies: ["PastoCore"]),
        .executableTarget(name: "PastoCoreTests", dependencies: ["PastoCore"], path: "Tests/PastoCoreTests")
    ]
)
