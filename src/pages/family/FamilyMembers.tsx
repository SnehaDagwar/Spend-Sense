import React, { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UserPlus, Trash2, Shield, User, Baby } from "lucide-react";
import { FamilyRole } from "@/types";
import { motion, AnimatePresence } from "framer-motion";

const RoleIcon = ({ role }: { role: FamilyRole }) => {
  switch (role) {
    case "Admin": return <Shield className="h-4 w-4 text-primary" />;
    case "Child": return <Baby className="h-4 w-4 text-accent" />;
    default: return <User className="h-4 w-4 text-secondary" />;
  }
};

const FamilyMembers = () => {
  const { familyMembers, addFamilyMember, removeFamilyMember } = useAppStore();
  const [isAdding, setIsAdding] = useState(false);
  const [newMember, setNewMember] = useState({ name: "", role: "Member" as FamilyRole });

  const handleAdd = () => {
    if (newMember.name.trim()) {
      addFamilyMember(newMember);
      setNewMember({ name: "", role: "Member" });
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold">Family Members</h1>
          <p className="text-muted-foreground mt-1">Manage who has access to the family wallet.</p>
        </div>
        <Button onClick={() => setIsAdding(true)} className="rounded-full shadow-glow">
          <UserPlus className="mr-2 h-4 w-4" /> Add Member
        </Button>
      </div>

      <AnimatePresence>
        {isAdding && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="p-6 mb-6 glass-card border-none">
              <h3 className="text-lg font-bold mb-4">Add New Member</h3>
              <div className="grid gap-4 md:grid-cols-3 items-end">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input 
                    value={newMember.name} 
                    onChange={(e) => setNewMember({ ...newMember, name: e.target.value })} 
                    placeholder="e.g. Sarah"
                    className="bg-white/50"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select 
                    value={newMember.role} 
                    onValueChange={(val: FamilyRole) => setNewMember({ ...newMember, role: val })}
                  >
                    <SelectTrigger className="bg-white/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Admin">Admin (Full Access)</SelectItem>
                      <SelectItem value="Member">Member (Add Expenses)</SelectItem>
                      <SelectItem value="Child">Child (Limited / Tracked)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleAdd} className="flex-1">Add</Button>
                  <Button variant="outline" onClick={() => setIsAdding(false)}>Cancel</Button>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {familyMembers.map((member) => (
          <Card key={member.id} className="p-5 glass-card border-none flex items-center justify-between group hover:shadow-lg transition-all duration-300">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border border-white/40">
                <span className="text-lg font-bold text-primary">{member.name.charAt(0)}</span>
              </div>
              <div>
                <h4 className="font-bold">{member.name}</h4>
                <div className="flex items-center gap-1.5 mt-0.5 text-xs text-muted-foreground bg-white/40 px-2 py-0.5 rounded-full w-fit">
                  <RoleIcon role={member.role} />
                  <span>{member.role}</span>
                </div>
              </div>
            </div>
            {member.role !== "Admin" && (
              <Button 
                variant="ghost" 
                size="icon" 
                className="opacity-0 group-hover:opacity-100 text-destructive hover:bg-destructive/10 hover:text-destructive transition-opacity"
                onClick={() => removeFamilyMember(member.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </Card>
        ))}
        {familyMembers.length === 0 && (
          <div className="col-span-full p-8 text-center text-muted-foreground bg-white/20 rounded-2xl border border-dashed border-white/40">
            No family members added yet. Add someone to start sharing expenses!
          </div>
        )}
      </div>
    </div>
  );
};

export default FamilyMembers;
