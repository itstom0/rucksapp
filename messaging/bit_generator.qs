namespace Messaging {
    open Microsoft.Quantum.Intrinsic;

    operation RandomBit() : Result {
        use q = Qubit();
        H(q);
        return MResetZ(q);
    }
}
