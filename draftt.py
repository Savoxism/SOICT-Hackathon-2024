import math

class Solution:
    def isPalindrome(self, s):
        joined_s = ''.join([char.lower() for char in s if char.isalnum()])
        
        if joined_s == joined_s[::-1]:
            return True
        
        return False
        


sol = Solution()
s = "aabbaa"

print(sol.isPalindrome(s))
