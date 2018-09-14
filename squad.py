class Squad:
    def __init__(self, members):
        try:
            self.members = set(members)
        except TypeError:
            self.members = {members}

    def add_member(self, member):
        assert member.squad is None
        self.members.add(member)
        member.squad = self

    def remove_member(self, member):
        assert member.squad == self
        self.members.remove(member)
        member.squad = None
