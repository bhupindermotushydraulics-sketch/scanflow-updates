import unittest
from prepare_update import CERTIFICATE, verify_signer_output


class SigningOutputTest(unittest.TestCase):
    def test_numbered_signer(self):
        verify_signer_output(f'Signer #1 certificate SHA-256 digest: {CERTIFICATE}\n')

    def test_scheme_signer_and_repeated_same_certificate(self):
        verify_signer_output(f'V2 Signer: certificate SHA-256 digest: {CERTIFICATE}\n')
        verify_signer_output(f'V2 Signer: certificate SHA-256 digest: {CERTIFICATE}\n'
                             f'V3 Signer: certificate SHA-256 digest: {CERTIFICATE.upper()}\n')

    def test_rejects_wrong_or_extra_signer(self):
        for output in [f'V2 Signer: certificate SHA-256 digest: {"0"*64}\n',
                       f'Signer #1 certificate SHA-256 digest: {CERTIFICATE}\n'
                       f'Signer #2 certificate SHA-256 digest: {"0"*64}\n']:
            with self.assertRaises(ValueError):
                verify_signer_output(output)

    def test_rejects_missing_or_truncated_certificate(self):
        for output in ['', 'Verification failed', f'V2 Signer: certificate SHA-256 digest: {CERTIFICATE[:-1]}\n']:
            with self.assertRaises(ValueError):
                verify_signer_output(output)


if __name__ == '__main__':
    unittest.main()
