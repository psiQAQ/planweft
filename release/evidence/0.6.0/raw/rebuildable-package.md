# 0.6.0 exact package evidence

- Source commit: `50082dcaa9da44df1e4343533c45c5e7617f3178`
- Package: `planweft@0.6.0`
- Archive: `planweft-0.6.0.tgz`
- Local archive SHA-256 (Node 22.22.1/npm 9.2.0): `c6af326b4da1d0d3c2814c7213461bfc7b7d2f5c65c80cf90ede643917970ebd`
- Candidate archive SHA-256 (trusted workflow 35241038823, Node 24.20.0/npm 11.11.0): `7e913d3c43e852aaf59dbb2fc7adb3b7aa275453cf3041ec1acdebea80be9c5e`
- Preparation command: `python3 scripts/prepare-native-release.py --release --output /tmp/planweft-release-0.6.0-20260917 --repository-url https://github.com/psiQAQ/planweft`
- Result: builder verify returned `verified: true`; release preparation returned `Prepared locally; not published`.
- The local and trusted-workflow pack reports both contain 4,893 entries and 46,560,650 unpacked bytes with the same path/size/mode manifest. The final admission hash is the trusted-workflow archive hash above because npm's tar serialization differs between the local and GitHub Node runtimes; the workflow logs both hashes and rejects any mismatch against this evidence.
- The archive manifest and generated distribution manifest identify the same `0.6.0` package; the candidate was generated from the clean merged `master` checkout.
