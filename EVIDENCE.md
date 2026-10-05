# Evidence: Warranty on GenLayer StudioNet

Every row below was read back from the chain by `scripts/evidence.mjs`: the
sender, the status and the outcome come from the node's answer for each hash,
not from the deployment record. Every outcome on chain matches the record.

- **Contract:** [`0x6fB2b29E061e06E95EFB1AF15e35b1cC1FE68Da8`](https://explorer-studio.genlayer.com/address/0x6fB2b29E061e06E95EFB1AF15e35b1cC1FE68Da8)
- **Deploy transaction:** [`0xf1772b8d…1c61`](https://explorer-studio.genlayer.com/tx/0xf1772b8dd9084ca53b57c36dd54c03643ae156f9352360be9f650bb51d7e1c61)
- **Source sha256:** `7c272a9d3f0ee539ec46cc419f4e929aada00881a4ed14e1b5ea8525bc140893`
- **Transactions:** 11, from 3 different wallets
- **Generated:** 2026-10-05 23:35 UTC

## Wallets

Each wallet was made in memory for this run, and its key was never written
anywhere. Click an address to see every transaction it sent.

| Role | Address | Transactions sent |
|---|---|---|
| seller | [`0xA10dc728Deb2623c9275a0c86dB8D0e85A77b03E`](https://explorer-studio.genlayer.com/address/0xA10dc728Deb2623c9275a0c86dB8D0e85A77b03E) | 3 |
| stranger | [`0x0BFD705617Bd7eaCd1DFa7964342231fFF9Dd700`](https://explorer-studio.genlayer.com/address/0x0BFD705617Bd7eaCd1DFa7964342231fFF9Dd700) | 2 |
| buyer | [`0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95`](https://explorer-studio.genlayer.com/address/0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95) | 6 |

## Transactions, in order

"refused" is a transaction the contract was meant to refuse: the committee
agreed on the refusal, and the sentence is the contract's own.

| # | Step | Sent by | Method | On chain | Outcome | Tx |
|---|---|---|---|---|---|---|
| 0 | deploy | seller [`0xA10d…b03E`](https://explorer-studio.genlayer.com/address/0xA10dc728Deb2623c9275a0c86dB8D0e85A77b03E) | `deploy` | FINALIZED · MAJORITY_AGREE | executed | [`0xf1772b8d…1c61`](https://explorer-studio.genlayer.com/tx/0xf1772b8dd9084ca53b57c36dd54c03643ae156f9352360be9f650bb51d7e1c61) |
| 1 | warranty 0 opened: three covered defects, every payout paid in | seller [`0xA10d…b03E`](https://explorer-studio.genlayer.com/address/0xA10dc728Deb2623c9275a0c86dB8D0e85A77b03E) | `open` | FINALIZED · MAJORITY_AGREE | executed | [`0xf1480f97…476a`](https://explorer-studio.genlayer.com/tx/0xf1480f97ec836702d02a9e76133e188cfac03754fdaec86d905c90d8568f476a) |
| 2 | a stranger claims | stranger [`0x0BFD…d700`](https://explorer-studio.genlayer.com/address/0x0BFD705617Bd7eaCd1DFa7964342231fFF9Dd700) | `claim` | FINALIZED · MAJORITY_AGREE | refused: only the buyer named in the warranty may claim | [`0x1a3dba37…a125`](https://explorer-studio.genlayer.com/tx/0x1a3dba37c99ed24b92d7e338eaffb9d1fb2d9bac38af0123a6dc46bd5d54a125) |
| 3 | the pump: covered defect 0, paid | buyer [`0x5Dcd…Fc95`](https://explorer-studio.genlayer.com/address/0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95) | `claim` | FINALIZED · MAJORITY_AGREE | executed | [`0xf25a3269…e1cc`](https://explorer-studio.genlayer.com/tx/0xf25a32698d1964ffd267481f24061e76e67f29ace71b3b68982a57e7f515e1cc) |
| 4 | the same account again | buyer [`0x5Dcd…Fc95`](https://explorer-studio.genlayer.com/address/0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95) | `claim` | FINALIZED · MAJORITY_AGREE | refused: this account was already decided as claim 0; that answer stands | [`0x49663ffe…05aa`](https://explorer-studio.genlayer.com/tx/0x49663ffe211ba9950e0b18d5f8512e968a10c2ba13a93af81625bf80f75005aa) |
| 5 | the boiler, after a fall: excluded, declined | buyer [`0x5Dcd…Fc95`](https://explorer-studio.genlayer.com/address/0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95) | `claim` | FINALIZED · MAJORITY_AGREE | executed | [`0x006142bf…e2f9`](https://explorer-studio.genlayer.com/tx/0x006142bfdf37f6e9a8393b43181e39c7181e7942d948923caeefeaef42b0e2f9) |
| 6 | the pump again: already paid | buyer [`0x5Dcd…Fc95`](https://explorer-studio.genlayer.com/address/0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95) | `claim` | FINALIZED · MAJORITY_AGREE | executed | [`0x66867ff0…c351`](https://explorer-studio.genlayer.com/tx/0x66867ff034404f21f11349a1e1a1ced59cff6e09dfa0a39fcefe72a4c7fcc351) |
| 7 | a fourth claim | buyer [`0x5Dcd…Fc95`](https://explorer-studio.genlayer.com/address/0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95) | `claim` | FINALIZED · MAJORITY_AGREE | refused: a warranty takes at most 3 claims | [`0x7af6e429…8891`](https://explorer-studio.genlayer.com/tx/0x7af6e4298d9810eb8967d6c135d09b7ac0272581ad9d05b0e5f6540ebc8f8891) |
| 8 | the seller releases before the end | seller [`0xA10d…b03E`](https://explorer-studio.genlayer.com/address/0xA10dc728Deb2623c9275a0c86dB8D0e85A77b03E) | `release` | FINALIZED · MAJORITY_AGREE | refused: the warranty runs until 2026-10-05T23:32:16Z | [`0x905b6ae7…ecad`](https://explorer-studio.genlayer.com/tx/0x905b6ae7e189f561b562156ce06582084300a6358ab45310c3dbedc1f19cecad) |
| 9 | a claim after the warranty ended | buyer [`0x5Dcd…Fc95`](https://explorer-studio.genlayer.com/address/0x5Dcd19bb0CAf65be1d8765398F3a52D6D244Fc95) | `claim` | FINALIZED · MAJORITY_AGREE | refused: the warranty ended at 2026-10-05T23:32:16Z; nothing can be claimed or ruled after it | [`0xcb8b0e1f…8cf3`](https://explorer-studio.genlayer.com/tx/0xcb8b0e1f11ae548861e0101dfd1eeac248c38dede79d6e75750321d2004b8cf3) |
| 10 | the rest released to the seller | stranger [`0x0BFD…d700`](https://explorer-studio.genlayer.com/address/0x0BFD705617Bd7eaCd1DFa7964342231fFF9Dd700) | `release` | FINALIZED · MAJORITY_AGREE | executed | [`0x4d4b5f87…90ca`](https://explorer-studio.genlayer.com/tx/0x4d4b5f871dc300890a66284832400950e684761d521aca6ac6eb0f75af3990ca) |
