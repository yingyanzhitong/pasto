<p align="center"><a href="README.md">简体中文</a> · <strong>English</strong></p>

<p align="center">
  <img src="replica/Assets/PastoIcon.png" width="112" alt="Pasto icon">
</p>

# Pasto

**A free, local clipboard manager for macOS.** Save what you copy, browse it as cards, and search and organize content you use often.

Pasto supports **macOS 14+, Intel (x86_64), and Apple silicon (arm64)**. It is built with Swift, AppKit, and SwiftUI and needs no account from the original vendor. The released 1.0.0 runs locally only. The current source includes a [CloudKit migration](docs/CLOUDKIT_MIGRATION.md) and a separate [iCloud Drive sync implementation](docs/ICLOUD_SYNC.md); neither is included in the published installer. Both linked guides are in Chinese.

[![Build and release](https://github.com/yingyanzhitong/pasto/actions/workflows/release.yml/badge.svg)](https://github.com/yingyanzhitong/pasto/actions/workflows/release.yml)

[Website](https://yingyanzhitong.github.io/pasto/) · [Download 1.0.0](https://github.com/yingyanzhitong/pasto/releases/tag/v1.0.0) · [Feature comparison](#paste-vs-pasto) · [Build from source](#build-from-source) · [Contribute](CONTRIBUTING.md) · [License scope](NOTICE.md)

Version 1.0.1 has been submitted for building: [view GitHub Actions](https://github.com/yingyanzhitong/pasto/actions/workflows/release.yml). Downloads will appear in [Releases](https://github.com/yingyanzhitong/pasto/releases) after publication succeeds. The website links above keep pointing to the published version.

## Screenshots

Actual app screenshots using isolated sample data, with no real clipboard history. The app interface shown is in Chinese.

Clipboard panel:

![Pasto clipboard panel](docs/images/pasto-panel.png)

Settings:

![Pasto settings](docs/images/pasto-settings.png)

## Features implemented in the source

- Clipboard history that preserves multiple content formats: text, images, files, links, and colors.
- A horizontal card panel, search and filters, multiple selection, previews, and local editing.
- Collections (Pinboard), a Pasto Stack queue, and archive import and export.
- Migration of local collections and their contents from Paste, preserving colors and order. Repeated imports do not overwrite existing edits. Open the More menu → Import collections from Paste…; see the [migration guide](replica/README.md#从-paste-迁移分组) (Chinese).
- Global keyboard shortcuts, configurable plain-text actions, recording pause, and local settings.
- Local Vision OCR and a separate `pasto-mcp` stdio service.

**Pasto is an independent implementation in development. Full one-to-one verification against the original is not complete.** The list above means source code and feature entry points exist; it does not mean every interaction or edge case has been verified. Cross-app direct paste has not been fully verified, so correct insertion at the cursor cannot be guaranteed in every app. When reporting copy or paste issues, include reproduction steps without private content.

## Paste vs. Pasto

**Pasto is free and open source, focused on local use on Mac.** ✅ Available · ❌ Not available

| Core feature | Paste | Pasto |
| --- | :---: | :---: |
| Clipboard history and content previews | ✅ | ✅ |
| Search and filters | ✅ | ✅ |
| Collections | ✅ | ✅ |
| Single and batch copy and paste | ✅ | ✅ |
| Sequential paste with Stack | ✅ | ✅ |
| Text recognition in images (OCR) | ✅ | ✅ |
| Custom keyboard shortcuts | ✅ | ✅ |
| AI tool integration (MCP) | ✅ | ✅ |
| Apple Shortcuts | ✅ | ❌ |
| iCloud sync and mobile apps | ✅ | ❌ |
| Shared collections and collaboration | ✅ | ❌ |
| Online link previews | ✅ | ❌ |

Pasto also supports [importing local collections from Paste](replica/README.md#从-paste-迁移分组). ✅ means implemented; full interactions and cross-app paste still need comprehensive verification. See the [feature and testing scope](replica/TESTING.md) (Chinese). This comparison covers Paste 6.6.6 and Pasto 1.0.0. For Paste's sync and collaboration features, see the [Paste website](https://pasteapp.io/).

## iCloud sync (unreleased source)

The **iCloud sync** settings include code migrated from the original CloudKit flow, using Pasto's own container and disabled by default. Valid Apple signing credentials and container configuration are currently missing, and live cloud testing is incomplete. It must not be advertised as a working feature yet. It does not connect to the original vendor's cloud data or provide mobile apps or shared collaboration.

The earlier iCloud Drive file sync implementation remains a separate option. It is not equivalent to CloudKit, and its upload results do not verify CloudKit behavior. See the [CloudKit notes](docs/CLOUDKIT_MIGRATION.md) (Chinese) for migration evidence, isolated tests, and outstanding work. The current 1.0.0 installer and the table above describe the released version.

## Download and use

Download from the [1.0.0 Release](https://github.com/yingyanzhitong/pasto/releases/tag/v1.0.0) and read its limitations. The installer is ad-hoc signed and has not been notarized by Apple.

Version 1.0.0 uses one installer for both Intel and Apple silicon:

[Download Pasto-1.0.0-macos-universal.dmg](https://github.com/yingyanzhitong/pasto/releases/download/v1.0.0/Pasto-1.0.0-macos-universal.dmg)

The main app, Helper, and MCP executable all include both architectures. There is no need to choose a chip-specific download. Check each older release's notes for its package format and supported architectures.

Open the DMG and drag `Pasto.app` onto the adjacent `Applications` shortcut. Launch Pasto from Applications after copying, then eject the disk image in Finder. Do not run the app from the disk image for everyday use.

Direct paste into other apps requires macOS Accessibility access. Granting permission does not mean the feature has passed full compatibility testing.

Pasto stores clipboard content locally. Screenshots, logs, and archives may contain personal information; review them before sharing. Prefer fictional text and temporary files when reproducing an issue.

## Build from source

You need macOS 14+, an Intel or Apple silicon Mac, Xcode Command Line Tools (the Swift toolchain), and Python 3. The build uses system frameworks and **does not download third-party Swift packages**.

```sh
git clone https://github.com/yingyanzhitong/pasto.git
cd pasto
bash replica/scripts/build-app.sh
open replica/dist/Pasto.app
```

By default, the build targets the architecture of your current Mac. The script creates `replica/dist/Pasto.app` with resources, a login helper, and the MCP executable, and checks local signatures.

Build one Universal DMG for both Apple silicon and Intel:

```sh
npm run build:dmg
```

This runs the release script's `release-ci.py package` command, builds both architectures, and combines them into one Universal DMG. To package an existing native-architecture app as a DMG:

```sh
bash replica/scripts/build-dmg.sh replica/dist/Pasto.app replica/dist/Pasto.dmg
```

DMG creation refuses to overwrite an existing destination file.

Compile for the current Mac without packaging an app:

```sh
swift build --package-path replica -c release
```

More development information is available in [replica/README.md](replica/README.md) and the [testing scope](replica/TESTING.md), both in Chinese.

## Automated builds and releases

Change `version` in the root `package.json` and push to `main` to trigger a GitHub Actions build and release when the version changes. You can also push a matching `v<version>` tag or run the workflow manually in Actions.

The workflow keeps a native Intel build check, then validates the Universal package's version, both architectures in all three executables, and signatures. It publishes three assets: `Pasto-<version>-macos-universal.dmg`, `SHA256SUMS.txt`, and `release-manifest.json`. The Release becomes public only after upload verification succeeds. Versions ending in `-dev.N` are prereleases; stable releases are marked as latest. A version does not overwrite artifacts from another commit, and failed runs do not publish a stable Release.

The `Source code (zip)` and `Source code (tar.gz)` links on a Release page are generated by GitHub for the tag. They are not installers or additional assets uploaded by this workflow.

See the [release workflow](.github/workflows/release.yml). A successful build and release does not imply successful functional regression testing.

## Project origins and verification limits

Pasto is independently rewritten using **Paste 6.6.6** static reverse-engineering evidence from REA / Ghidra. Decompiled pseudocode is not a directly buildable original Swift project. This project is not affiliated with or endorsed by the original vendor, and does not modify the original app or its licensing.

The existing original machine-code analysis and address evidence are from **arm64**. Providing one Universal DMG with both architectures does not mean the original x86_64 app has been decompiled or that all features have passed regression testing on Intel and Apple silicon.

See the [reverse-engineering notes](docs/REVERSE_ENGINEERING.md) for the research process and the [consolidated feature audit](reports/replica/fast-coverage-audit.md) for current evidence and remaining differences; both are in Chinese. Binary address counts, exported pseudocode counts, and registered implementation counts cannot be converted into a product completion percentage. A successful build, installation, or individual action also does not constitute full interaction verification.

## Open-source license

The independently written implementation, tools, documentation, and newly created Pasto icon are open source under the [MIT License](LICENSE). **This license does not cover decompiled output from the original app, recovered assembly, original localization resources, or other original materials.** See [NOTICE.md](NOTICE.md) for the scope and rights applicable to each part.
