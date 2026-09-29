cask "macfan" do
  version "0.2.0"
  sha256 "f3ca26019bb2166cd83cdf236a0b0545e5a2593d859866764867e6c4339d9d5e"

  url "https://github.com/greatyingzi/macfan/releases/download/v#{version}/macfan-#{version}.dmg"
  name "macfan"
  desc "Menu bar fan control and AppleSMC utility"
  homepage "https://github.com/greatyingzi/macfan"

  app "macfan.app"

  zap trash: [
    "~/Library/Application Support/macfan",
    "~/Library/LaunchAgents/com.macfan.menubar.plist",
  ]
end
