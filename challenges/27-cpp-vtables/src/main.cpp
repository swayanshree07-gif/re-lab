// 27-cpp-vtables (spoiler!). A factory builds one Stage object per 4-byte
// chunk; the virtual call through each object's vtable picks the transform.
#include <cstdio>
#include <cstring>
#include "params.h"

class Stage {
public:
    Stage(unsigned char a, unsigned char b, const unsigned char *t) : a_(a), b_(b), t_(t) {}
    virtual ~Stage() {}
    virtual unsigned char transform(unsigned char c, int i) const = 0;
    virtual const char *name() const = 0;
    bool check(const unsigned char *p) const {
        int bad = 0;
        for (int i = 0; i < 4; i++) bad |= transform(p[i], i) ^ t_[i];
        return bad == 0;
    }
protected:
    unsigned char a_, b_;
    const unsigned char *t_;
};

class RotStage : public Stage {
public:
    using Stage::Stage;
    unsigned char transform(unsigned char c, int i) const override {
        int r = (a_ + i) & 7;
        return (unsigned char)((c << r) | (c >> ((8 - r) & 7)));
    }
    const char *name() const override { return "rot"; }
};

class AddStage : public Stage {
public:
    using Stage::Stage;
    unsigned char transform(unsigned char c, int i) const override { return c + a_ + i * b_; }
    const char *name() const override { return "add"; }
};

class XorStage : public Stage {
public:
    using Stage::Stage;
    unsigned char transform(unsigned char c, int i) const override {
        return c ^ (unsigned char)(a_ * (i + 1)) ^ b_;
    }
    const char *name() const override { return "xor"; }
};

class MulStage : public AddStage {   // inherits from AddStage, overrides transform
public:
    using AddStage::AddStage;
    unsigned char transform(unsigned char c, int i) const override {
        (void)i;
        return c * a_ + b_;
    }
};

static Stage *make_stage(const StageParams &p) {
    switch (p.kind) {
    case 0: return new RotStage(p.a, p.b, p.target);
    case 1: return new AddStage(p.a, p.b, p.target);
    case 2: return new XorStage(p.a, p.b, p.target);
    default: return new MulStage(p.a, p.b, p.target);
    }
}

int main() {
    char buf[128];
    std::printf("Password: ");
    std::fflush(stdout);
    if (!std::fgets(buf, sizeof buf, stdin)) return 1;
    buf[std::strcspn(buf, "\n")] = 0;
    bool ok = std::strlen(buf) == PW_LEN;
    Stage *stages[N_STAGES];
    for (int s = 0; s < N_STAGES; s++) stages[s] = make_stage(stage_params[s]);
    for (int s = 0; s < N_STAGES; s++) {
        if (ok) ok = stages[s]->check((const unsigned char *)buf + 4 * s);
        delete stages[s];
    }
    std::puts(ok ? "Correct!" : "Wrong.");
    return ok ? 0 : 1;
}
