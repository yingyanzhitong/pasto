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
        .target(name: "PastoObjC", publicHeadersPath: "include"),
        .target(name: "PastoCore", dependencies: ["PastoObjC"], resources: [.process("Resources")]),
        .executableTarget(name: "Pasto", dependencies: ["PastoCore", "PastoObjC"]),
        .executableTarget(name: "PastoHelper"),
        .executableTarget(name: "PastoMCP", dependencies: ["PastoCore"]),
        .executableTarget(name: "PastoCoreTests", dependencies: ["PastoCore"], path: "Tests/PastoCoreTests")
    ]
)
