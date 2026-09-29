cask "macfan" do
  version "0.2.5"
  sha256 "e9fd7c5657e9da4e241220ee771d3f9cdb657d8d9cd2845748b91476b176a36b"

  url "https://github.com/greatyingzi/macfan/releases/download/v#{version}/macfan-#{version}.dmg"
  name "macfan"
  desc "Menu bar fan control and AppleSMC utility"
  homepage "https://github.com/greatyingzi/macfan"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "macfan.app"

  caveats <<~EOS
    macfan is ad-hoc signed rather than notarised, so macOS quarantines it and
    the first launch needs one approval:

      xattr -dr com.apple.quarantine /Applications/macfan.app

    ...or open System Settings > Privacy & Security and allow it there.
    Homebrew 7 removed its no-quarantine flag, so that is the only route.
  EOS

  zap trash: [
    "~/Library/Application Support/macfan",
    "~/Library/LaunchAgents/com.macfan.menubar.plist",
  ]
end
