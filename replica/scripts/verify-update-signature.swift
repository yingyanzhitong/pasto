import CryptoKit
import Foundation

// Only public material is passed on the command line.
let arguments = CommandLine.arguments
guard arguments.count == 4,
      let publicBytes = Data(base64Encoded: try String(contentsOfFile: arguments[1], encoding: .utf8)
        .trimmingCharacters(in: .whitespacesAndNewlines)),
      let signature = Data(base64Encoded: arguments[2]) else {
    throw NSError(domain: "PastoUpdates", code: 1)
}
let publicKey = try Curve25519.Signing.PublicKey(rawRepresentation: publicBytes)
let archive = try Data(contentsOf: URL(fileURLWithPath: arguments[3]), options: .mappedIfSafe)
guard publicKey.isValidSignature(signature, for: archive) else {
    throw NSError(domain: "PastoUpdates", code: 2,
                  userInfo: [NSLocalizedDescriptionKey: "Update key does not match the public key embedded in Pasto."])
}
