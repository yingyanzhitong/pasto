// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PasteReplica",
    defaultLocalization: "en",
    platforms: [.macOS(.v14)],
    products: [
        .library(name: "PasteReplicaCore", targets: ["PasteReplicaCore"]),
        .executable(name: "PasteReplica", targets: ["PasteReplica"]),
        .executable(name: "PasteReplicaHelper", targets: ["PasteReplicaHelper"]),
        .executable(name: "paste-replica-mcp", targets: ["PasteReplicaMCP"]),
        .executable(name: "paste-replica-core-tests", targets: ["PasteReplicaCoreTests"])
    ],
    targets: [
        .target(name: "PasteReplicaObjC", publicHeadersPath: "include"),
        .target(name: "PasteReplicaCore", dependencies: ["PasteReplicaObjC"], resources: [.process("Resources")]),
        .executableTarget(name: "PasteReplica", dependencies: ["PasteReplicaCore", "PasteReplicaObjC"]),
        .executableTarget(name: "PasteReplicaHelper"),
        .executableTarget(name: "PasteReplicaMCP", dependencies: ["PasteReplicaCore"]),
        .executableTarget(name: "PasteReplicaCoreTests", dependencies: ["PasteReplicaCore"], path: "Tests/PasteReplicaCoreTests")
    ]
)
